import random
import sys
import sqlite3
import hashlib
from _datetime import datetime, timedelta

from PyQt6 import uic
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QDialog


class MainMenu(QMainWindow):
    def __init__(self):
        super().__init__()
        # Загрузка дизайна
        self.current_theme = "light"  # По умолчанию светлая тема
        self.RegWindow = RegWindow(self)
        self.UspRegWindow = UspRegWindow()
        uic.loadUi('menu.ui', self)
        self.setWindowTitle('Menu')
        self.VhodButton.clicked.connect(self.vhod)
        self.RegButton.clicked.connect(self.registracia)

    def apply_theme(self, theme_file):
        """Применяет тему для всего приложения."""
        with open(theme_file, "r") as file:
            style = file.read()
            QApplication.instance().setStyleSheet(style)

    def switch_theme(self):
        """Переключает тему и применяет её."""
        if self.current_theme == "light":
            self.apply_theme("dark_theme.qss")
            self.current_theme = "dark"
        else:
            self.apply_theme("light_theme.qss")
            self.current_theme = "light"

    def vhod(self):
        log = self.lineEdit.text()
        password = self.lineEdit_2.text()
        if log and password:
            # кеширование данных
            hashed_log = hashlib.sha256(log.encode('utf-8')).hexdigest()
            hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
            con = sqlite3.connect('UsersInfo.db')
            cur = con.cursor()
            res = cur.execute("""SELECT * FROM users
                            WHERE UserLogin = ? and UserPassword = ?""", (hashed_log, hashed_password,)).fetchall()
            if res:
                UserLogin = res[0][1]
                UserPassword = res[0][2]
                UserKeys = res[0][4]
                UserName = res[0][3]
                self.OsnWindow = WeeklyPlannerWindow(UserLogin, UserPassword, UserKeys, UserName, self)
                self.OsnWindow.show()
                self.close()
            else:
                self.statusbar.showMessage('Неверный логин или пароль!', 5000)
            con.close()
        else:
            self.statusbar.showMessage('Поле логина или пароля пустые!', 5000)

    def registracia(self):
        self.RegWindow.show()
        self.close()


class RegWindow(QMainWindow):
    def __init__(self, main_menu):
        super().__init__()
        self.main_menu = main_menu
        # Загрузка дизайна
        uic.loadUi('RegW.ui', self)
        self.setWindowTitle('Registration')
        self.pushButton.clicked.connect(self.registracia_r)

    def registracia_r(self):
        log = self.LogLineEdit.text()
        pas = self.PasLineEdit.text()
        name = self.NameLineEdit.text()
        # кешируем
        if log and pas and name:
            log = hashlib.sha256(log.encode('utf-8')).hexdigest()
            pas = hashlib.sha256(pas.encode('utf-8')).hexdigest()
            con = sqlite3.connect('UsersInfo.db')
            cur = con.cursor()
            result = cur.execute("""SELECT * FROM users
                                        WHERE UserLogin = ?""", (log,)).fetchall()
            if not result:
                max_id_result = cur.execute("""SELECT MAX(id) FROM users""").fetchone()
                new_id = (max_id_result[0] or 0) + 1
                week_days = ', '.join(str(x) for x in range(new_id * 21 - 20, new_id * 21 + 1))
                result1 = cur.execute(
                    """INSERT INTO users(UserLogin,UserPassword,UserName,WeekDays) VALUES(?,?,?,?)""",
                    (log, pas, name, week_days))
                days = [(i, log, '') for i in range(1, 22)]
                cur.executemany("INSERT INTO days (DayNumber, UserLogin, Events) VALUES (?, ?, ?)", days)
                con.commit()
                self.Mm = MainMenu()
                self.Mm.show()
                self.Urw = UspRegWindow()
                self.Urw.show()
                self.close()
            else:
                self.statusbar.showMessage('Этот логин занят!', 5000)
        else:
            self.statusbar.showMessage('Логин, пароль или имя пустые!', 5000)
        con.close()


class WeeklyPlannerWindow(QMainWindow):
    def __init__(self, UserLogin, UserPassword, WeekDays, UserName, main_menu):
        super().__init__()
        self.UserLogin = UserLogin
        self.main_menu = main_menu
        self.UserName = UserName
        uic.loadUi('WeeklyPlannerTheWeek.ui', self)
        self.setWindowTitle('WeeklyPlanner')

        # Подключение кнопок
        self.SetButton.clicked.connect(self.openSet)
        self.EvrDButton.clicked.connect(self.openEvrydayTasks)
        self.LWButton.clicked.connect(self.LastWeekop)
        self.NWButton.clicked.connect(self.NextWeekop)

        # Поля ввода событий для каждого дня (QTextEdit)
        self.day_event_inputs = [
            self.eventMonday, self.eventTuesday, self.eventWednesday,
            self.eventThursday, self.eventFriday, self.eventSaturday, self.eventSunday
        ]

        # Подключаем сигнал textChanged для каждого поля
        for day_index, text_edit in enumerate(self.day_event_inputs):
            text_edit.textChanged.connect(lambda idx=day_index: self.save_event_for_day(idx))

        # Инициализация переменных для управления неделями
        self.current_week = 2  # 2 - текущая неделя, 1 - предыдущая, 3 - следующая
        self.total_weeks = 3  # Общее количество доступных недель

        # Заполняем начальные данные
        self.fill_dates()
        # Режим приветствия/цитат
        self.is_greeting_mode = True  # True: приветствие, False: цитаты
        self.quotes = [
            "Настоящий мужчина и так знает, что нельзя",
            "Не круто пить, не круто врать, круто маме помогать",
            "«Жи-ши» пиши от души",
            "Кто обзывается, тот сам так называется",
            "По-настоящему несгибаемым делает межпозвоночная грыжа",
            "Позвоночник знаешь? Я позвонил",
            "Будь джедаем, осталось немного",
            "Между первой и второй перерывчик небольшой",
            "Работа не волк. Никто не волк. Только волк — волк",
            "В моей руке граната без чеки - на подержи"
        ]

        self.update_display()  # Изначальное состояние

    def update_display(self):
        """Обновляет текст приветствия или выводит случайную цитату."""
        if self.is_greeting_mode:
            self.labelWelcome.setText(f"Приветствуем вас, {self.UserName}!")  # Приветствие
        else:
            self.labelWelcome.setText(random.choice(self.quotes))  # Случайная цитата

    def toggle_greeting_mode(self):
        """Переключает режим между приветствием и цитатами."""
        self.is_greeting_mode = not self.is_greeting_mode
        self.update_display()

    def fill_dates(self):
        week_start = (self.current_week - 1) * 7 + 1  # Сдвигаем недели на 1 для текущей
        day_numbers = list(range(week_start, week_start + 7))

        # Проверка допустимости номеров дней
        day_numbers = [num for num in day_numbers if 1 <= num <= 21]

        con = sqlite3.connect('UsersInfo.db')
        cur = con.cursor()

        if len(day_numbers) == 7:  # Только если у нас есть полный набор дней
            days = cur.execute(
                "SELECT DayNumber, Events FROM days WHERE UserLogin = ? AND DayNumber IN (?, ?, ?, ?, ?, ?, ?)",
                (self.UserLogin, *day_numbers)
            ).fetchall()
        else:
            days = []
        con.close()


        # Устанавливаем задачи в соответствующие QTextEdit
        for day_index, text_edit in enumerate(self.day_event_inputs):
            if day_index < len(day_numbers):  # Проверяем, что индекс в пределах допустимого
                day_number = day_numbers[day_index]
                event_text = next((day[1] for day in days if day[0] == day_number), '')
                text_edit.setPlainText(event_text)
            else:
                text_edit.setPlainText('')  # Очищаем поле, если номер дня недоступен

        # Обновляем отображение дат
        self.update_week_dates(week_start)
        self.update_buttons()

    def update_week_dates(self, week_start):
        """Обновляет отображение дат в интерфейсе."""
        today = datetime.today()
        weekday_index = today.weekday()
        start_of_week = today - timedelta(days=weekday_index)

        # Учитываем текущую неделю
        start_of_week += timedelta(weeks=self.current_week - 2)

        # Заполняем каждое поле датой
        date_widgets = [
            self.dateMonday, self.dateTuesday, self.dateWednesday,
            self.dateThursday, self.dateFriday, self.dateSaturday, self.dateSunday
        ]

        years = set()
        for i, widget in enumerate(date_widgets):
            day_date = start_of_week + timedelta(days=i)
            formatted_date = day_date.strftime('%d.%m')
            widget.setText(formatted_date)
            years.add(day_date.year)

        # Обновляем год
        year_display = f"{min(years)}-{max(years)}" if len(years) > 1 else str(min(years))
        self.labelYear.setText(f'Год: {year_display}')

    def update_buttons(self):
        # Управление кнопками "назад" и "вперёд"
        if self.current_week == 1:  # Если на предыдущей неделе
            self.LWButton.setEnabled(False)
            self.LWButton.setText('-')
        else:
            self.LWButton.setEnabled(True)
            self.LWButton.setText('<-')

        if self.current_week == 3:  # Если на следующей неделе
            self.NWButton.setEnabled(False)
            self.NWButton.setText('-')
        else:
            self.NWButton.setEnabled(True)
            self.NWButton.setText('->')

    def LastWeekop(self):
        if self.current_week > 1:  # Проверяем, чтобы не выйти за пределы
            self.current_week -= 1
            self.fill_dates()

    def NextWeekop(self):
        if self.current_week < 3:  # Проверяем, чтобы не выйти за пределы
            self.current_week += 1
            self.fill_dates()

    def openSet(self):
        self.Sm = SettingsMenu(self.main_menu, self)
        self.Sm.show()
        self.close()

    def openEvrydayTasks(self):
        self.Rz = RegZad(self)
        self.Rz.show()
        self.close()

    def shift_weeks(self):
        con = sqlite3.connect('UsersInfo.db')
        cur = con.cursor()

        days = cur.execute(
            "SELECT id, DayNumber, Events FROM days WHERE UserLogin = ? ORDER BY DayNumber",
            (self.UserLogin,)
        ).fetchall()

        if len(days) == 21:
            # Первая неделя -> Вторая неделя
            for i in range(7):
                cur.execute("UPDATE days SET Events = ? WHERE id = ?", (days[i + 7][2], days[i][0]))

            # Вторая неделя -> Третья неделя
            for i in range(7, 14):
                cur.execute("UPDATE days SET Events = ? WHERE id = ?", (days[i + 7][2], days[i][0]))

            # Третья неделя очищается
            for i in range(14, 21):
                cur.execute("UPDATE days SET Events = '' WHERE id = ?", (days[i][0],))

            con.commit()
        con.close()

    def save_event_for_day(self, day_index):
        week_start = (self.current_week - 1) * 7 + 1
        day_number = week_start + day_index
        event_text = self.day_event_inputs[day_index].toPlainText()

        con = sqlite3.connect('UsersInfo.db')
        cur = con.cursor()
        cur.execute(
            "UPDATE days SET Events = ? WHERE UserLogin = ? AND DayNumber = ?",
            (event_text, self.UserLogin, day_number)
        )
        con.commit()
        con.close()

    def save_event(self, day_number, event_text):
        con = sqlite3.connect('UsersInfo.db')
        cur = con.cursor()

        # Проверяем, существует ли день в базе данных
        existing_day = cur.execute(
            "SELECT DayNumber FROM days WHERE UserLogin = ? AND DayNumber = ?",
            (self.UserLogin, day_number)
        ).fetchone()

        if existing_day:
            # Обновляем событие
            cur.execute(
                "UPDATE days SET Events = ? WHERE UserLogin = ? AND DayNumber = ?",
                (event_text, self.UserLogin, day_number)
            )
        else:
            print(f"День с номером {day_number} не найден для пользователя {self.UserLogin}!")

        con.commit()
        con.close()

    def update_everyday_tasks(self):
        """Обновляет ежедневные задачи в текстовых полях."""
        con = sqlite3.connect('UsersInfo.db')
        cur = con.cursor()

        # Загружаем ежедневные задачи
        everyday_tasks = cur.execute(
            "SELECT Task FROM everyday_tasks WHERE UserLogin = ?",
            (self.UserLogin,)
        ).fetchall()
        everyday_tasks = [task[0] for task in everyday_tasks]  # Извлекаем текст задач

        # Добавляем ежедневные задачи в начало задач каждого дня
        for day_index, text_edit in enumerate(self.day_event_inputs):
            current_text = text_edit.toPlainText().strip()  # Получаем текущий текст
            updated_text = "\n".join(everyday_tasks)  # Ежедневные задачи
            if current_text:  # Если есть задачи, добавляем их после ежедневных
                updated_text += f"\n{current_text}"
            text_edit.setPlainText(updated_text)

        con.close()
        QMessageBox.information(self, "Успех", "Ежедневные задачи обновлены!")


class SettingsMenu(QMainWindow):
    def __init__(self, main_menu, weekly_planner_window):
        super().__init__()
        self.main_menu = main_menu
        self.weekly_planner_window = weekly_planner_window
        uic.loadUi('SettingsMenu.ui', self)
        self.setWindowTitle('SettingsMenu')
        self.ThemeButton.clicked.connect(self.change_theme)
        self.YourThemeButton.clicked.connect(self.set_custom_background)
        self.CloseAkkButton.clicked.connect(self.close_account)
        self.CorTButton.clicked.connect(self.switch_display_mode)
        self.BackButton.clicked.connect(self.go_back_to_weekly_planner)

    def change_theme(self):
        self.main_menu.switch_theme()

    def set_custom_background(self):
        # Диалог для выбора файла
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self.apply_custom_background(file_path)

    def apply_custom_background(self, file_path):
        # Установка выбранного изображения в качестве фона
        try:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                QMessageBox.warning(self, "Ошибка", "Выбранный файл не является изображением!")
                return

            # Формируем QSS для задания фонового изображения
            background_style = f"""
            QMainWindow {{
                background-image: url({file_path});
                background-repeat: no-repeat;
                background-position: center;
                background-size: cover;
            }}
            """
            QApplication.instance().setStyleSheet(background_style)
            QMessageBox.information(self, "Успех", "Фон успешно установлен!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось установить фон: {e}")

    def close_account(self):
        self.main_menu = MainMenu()
        self.main_menu.show()
        self.close()

    def switch_display_mode(self):
        """Переключает режим приветствия/цитат в WeeklyPlannerWindow."""
        if isinstance(self.weekly_planner_window, WeeklyPlannerWindow):
            self.weekly_planner_window.toggle_greeting_mode()

    def go_back_to_weekly_planner(self):
        """Возвращаемся в WeeklyPlannerWindow."""
        self.weekly_planner_window.show()
        self.close()


class RegZad(QMainWindow):
    def __init__(self, weekly_planner_window):
        super().__init__()
        uic.loadUi('RegZad.ui', self)
        self.setWindowTitle('Everyday tasks')
        self.weekly_planner_window = weekly_planner_window

        # Кнопки
        self.BackButton.clicked.connect(self.go_back)
        self.AddButton.clicked.connect(self.open_add_window)
        self.DeleteButton.clicked.connect(self.open_delete_window)
        self.RefreshButton.clicked.connect(self.refresh_tasks)

        self.load_everyday_tasks()

    def load_everyday_tasks(self):
        con = sqlite3.connect('UsersInfo.db')
        cur = con.cursor()

        # Получаем список задач пользователя
        tasks = cur.execute(
            "SELECT Task FROM everyday_tasks WHERE UserLogin = ?",
            (self.weekly_planner_window.UserLogin,)
        ).fetchall()
        con.close()

        self.EverydayTasksText.clear()  # Очищаем список перед добавлением новых данных

        # Добавляем задачи в виджет
        for task in tasks:
            self.EverydayTasksText.addItem(task[0])

    def refresh_tasks(self):
        tasks = []
        for i in range(self.EverydayTasksText.count()):
            tasks.append(self.EverydayTasksText.item(i).text().strip())

        con = sqlite3.connect('UsersInfo.db')
        cur = con.cursor()

        # Шаг 1: Обновляем таблицу `everyday_tasks`
        cur.execute("DELETE FROM everyday_tasks WHERE UserLogin = ?", (self.weekly_planner_window.UserLogin,))
        for task in tasks:
            if task:
                cur.execute("INSERT INTO everyday_tasks (UserLogin, Task) VALUES (?, ?)",
                            (self.weekly_planner_window.UserLogin, task))

        everyday_tasks_str = "\n".join(tasks)

        for day in range(1, 22):
            current_tasks = cur.execute(
                "SELECT Events FROM days WHERE UserLogin = ? AND DayNumber = ?",
                (self.weekly_planner_window.UserLogin, day)
            ).fetchone()

            if current_tasks and current_tasks[0]:
                updated_tasks = everyday_tasks_str + "\n" + current_tasks[0]
            else:
                updated_tasks = everyday_tasks_str

            cur.execute(
                "UPDATE days SET Events = ? WHERE UserLogin = ? AND DayNumber = ?",
                (updated_tasks.strip(), self.weekly_planner_window.UserLogin, day)
            )

        con.commit()
        con.close()

        QMessageBox.information(self, "Успех", "Ежедневные задачи обновлены и добавлены первыми!")

    def open_add_window(self):
        self.Aw = AddWind(self)
        self.Aw.show()

    def open_delete_window(self):
        self.Dw = DelWind(self)
        self.Dw.show()

    def go_back(self):
        self.weekly_planner_window.show()
        self.close()


class AddWind(QMainWindow):
    def __init__(self, reg_zad_window):
        super().__init__()
        uic.loadUi('AddWind.ui', self)
        self.setWindowTitle('Add Tasks')
        self.reg_zad_window = reg_zad_window

        # Кнопки
        self.AddTaskButton.clicked.connect(self.add_task)
        self.BackButton.clicked.connect(self.go_back)

    def add_task(self):
        new_task = self.NewTaskText.toPlainText().strip()
        if not new_task:
            QMessageBox.warning(self, "Ошибка", "Введите текст задачи!")
            return

        con = sqlite3.connect('UsersInfo.db')
        cur = con.cursor()
        cur.execute("INSERT INTO everyday_tasks (UserLogin, Task) VALUES (?, ?)",
                    (self.reg_zad_window.weekly_planner_window.UserLogin, new_task))
        con.commit()
        con.close()

        self.reg_zad_window.EverydayTasksText.addItem(new_task)

        QMessageBox.information(self, "Успех", "Задача добавлена!")
        self.go_back()

    def go_back(self):
        """Возвращается в окно ежедневных задач."""
        self.close()
        self.reg_zad_window.show()


class DelWind(QMainWindow):
    def __init__(self, reg_zad_window):
        super().__init__()
        uic.loadUi('DelWind.ui', self)
        self.setWindowTitle('Delete Tasks')
        self.reg_zad_window = reg_zad_window

        # Кнопки
        self.DeleteTaskButton.clicked.connect(self.delete_task)
        self.BackButton.clicked.connect(self.go_back)

        self.load_tasks()

    def load_tasks(self):
        """Загружает задачи в список для выбора."""
        tasks = [self.reg_zad_window.EverydayTasksText.item(i).text() for i in
                 range(self.reg_zad_window.EverydayTasksText.count())]

        self.TasksListWidget.clear()  # Очищаем список задач перед загрузкой новых
        self.TasksListWidget.addItems(tasks)  # Добавляем задачи в виджет списка

    def delete_task(self):
        current_index = self.TasksListWidget.currentIndex()  # Получаем индекс выбранного элемента
        if current_index == -1:  # Проверяем, если ничего не выбрано
            QMessageBox.warning(self, "Ошибка", "Выберите задачу для удаления!")
            return

        # Получаем текст задачи
        task_text = self.TasksListWidget.currentText()

        # Удаляем задачу из базы данных
        con = sqlite3.connect('UsersInfo.db')
        cur = con.cursor()
        cur.execute("DELETE FROM everyday_tasks WHERE UserLogin = ? AND Task = ?",
                    (self.reg_zad_window.weekly_planner_window.UserLogin, task_text))
        con.commit()
        con.close()

        self.TasksListWidget.removeItem(current_index)

        # Также удаляем из `EverydayTasksText` в основном окне
        for i in range(self.reg_zad_window.EverydayTasksText.count()):
            if self.reg_zad_window.EverydayTasksText.item(i).text() == task_text:
                self.reg_zad_window.EverydayTasksText.takeItem(i)
                break

        QMessageBox.information(self, "Успех", "Задача удалена!")

    def go_back(self):
        """Возвращается в окно ежедневных задач."""
        self.close()
        self.reg_zad_window.show()


class UspRegWindow(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('UspReg.ui', self)
        self.setWindowTitle('Successful registration')
        self.pushButton.clicked.connect(self.close)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Устанавливаем начальную тему
    with open("light_theme.qss", "r") as file:
        app.setStyleSheet(file.read())
    menu = MainMenu()
    menu.show()
    sys.exit(app.exec())
