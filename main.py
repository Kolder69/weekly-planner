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
            print(1)
            self.apply_theme("dark_theme.qss")
            self.current_theme = "dark"
        else:
            print(1)
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
                start_date = datetime.today() - timedelta(days=datetime.today().weekday() + 7)  # Неделя до текущей
                days = [
                    (start_date + timedelta(days=i), log, '')  # log - зашифрованный логин пользователя
                    for i in range(21)
                ]
                cur.executemany("""INSERT INTO days (DayDate, UserLogin, Events) VALUES (?, ?, ?)""", days)
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
        self.current_week = 0  # 0 - текущая неделя, -1 - предыдущая, +1 - следующая
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
        self.shift_weeks()
        # Определяем понедельник текущей недели
        today = datetime.today()
        weekday_index = today.weekday()
        start_of_week = today - timedelta(days=weekday_index)

        # Вычисляем сдвиг недели
        start_of_week += timedelta(weeks=self.current_week)

        # Список виджетов для заполнения
        date_widgets = [
            self.dateMonday, self.dateTuesday, self.dateWednesday,
            self.dateThursday, self.dateFriday, self.dateSaturday, self.dateSunday
        ]

        # Заполняем каждое поле датой соответствующего дня
        years = set()
        for i, widget in enumerate(date_widgets):
            day_date = start_of_week + timedelta(days=i)
            formatted_date = day_date.strftime('%d.%m')  # Формат день.месяц
            widget.setText(formatted_date)
            years.add(day_date.year)

        # Обновляем отображение года
        year_display = f"{min(years)}-{max(years)}" if len(years) > 1 else str(min(years))
        self.labelYear.setText(f'Год: {year_display}')

        # Обновляем состояние кнопок
        self.update_buttons()

    def update_buttons(self):
        # Управление кнопками "назад" и "вперёд"
        if self.current_week == -1:  # Если на предыдущей неделе
            self.LWButton.setEnabled(False)
            self.LWButton.setText('-')
        else:
            self.LWButton.setEnabled(True)
            self.LWButton.setText('<-')

        if self.current_week == 1:  # Если на следующей неделе
            self.NWButton.setEnabled(False)
            self.NWButton.setText('-')
        else:
            self.NWButton.setEnabled(True)
            self.NWButton.setText('->')

    def LastWeekop(self):
        if self.current_week > -1:  # Проверяем, чтобы не выйти за пределы
            self.current_week -= 1
            self.fill_dates()

    def NextWeekop(self):
        if self.current_week < 1:  # Проверяем, чтобы не выйти за пределы
            self.current_week += 1
            self.fill_dates()

    def openSet(self):
        self.Sm = SettingsMenu(self.main_menu, self)
        self.Sm.show()
        self.close()


    def openEvrydayTasks(self):
        pass

    def shift_weeks(self):
        con = sqlite3.connect('UsersInfo.db')
        cur = con.cursor()

        # Получить все дни для текущего пользователя
        days = cur.execute("""SELECT id, DayDate, Events FROM days WHERE UserLogin = ? ORDER BY DayDate""",
                           (self.UserName,)).fetchall()

        if len(days) == 21:
            # Сдвиг дней
            for i in range(7):  # Первая неделя становится второй
                cur.execute("""UPDATE days SET DayDate = ?, Events = ? WHERE id = ?""",
                            (days[i + 7][1], days[i + 7][2], days[i][0]))

            for i in range(7, 14):  # Вторая неделя становится третьей
                cur.execute("""UPDATE days SET DayDate = ?, Events = ? WHERE id = ?""",
                            (days[i + 7][1], days[i + 7][2], days[i][0]))

            # Третья неделя сбрасывается
            start_date = days[13][1] + timedelta(days=1)
            for i in range(14, 21):
                new_date = start_date + timedelta(days=i - 14)
                cur.execute("""UPDATE days SET DayDate = ?, Events = '' WHERE id = ?""", (new_date, days[i][0]))

            con.commit()
        con.close()

    def save_event_for_day(self, day_index):
        # Получаем текст из соответствующего QTextEdit
        event_text = self.day_event_inputs[day_index].toPlainText()

        # Сохраняем событие в базу данных
        self.save_event(day_index, event_text)

        # Опционально: Логирование или уведомление в статус-баре
        self.statusbar.showMessage(f"Событие для {self.day_names[day_index]} сохранено!", 2000)

    def save_event(self, day_index, event_text):
        # Индекс дня преобразуется в дату на основе текущей недели
        con = sqlite3.connect('UserDaysInfo.db')
        cur = con.cursor()

        # Находим дату соответствующего дня
        today = datetime.today()
        weekday_index = today.weekday()
        start_of_week = today - timedelta(days=weekday_index)
        target_date = start_of_week + timedelta(days=day_index)

        formatted_date = target_date.strftime('%Y-%m-%d')

        # Обновляем событие в таблице UserDays
        cur.execute("""
            UPDATE UserDays
            SET EventText = ?
            WHERE UserLogin = ? AND Date = ?;
        """, (event_text, self.UserLogin, formatted_date))

        con.commit()
        con.close()


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


class UspRegWindow(QDialog):
    def __init__(self):
        super().__init__()
        # Загружаем дизайн
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