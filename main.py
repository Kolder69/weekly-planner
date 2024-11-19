import sys
import sqlite3
import hashlib
from _datetime import datetime, timedelta

from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QDialog


class MainMenu(QMainWindow):
    def __init__(self):
        super().__init__()
        # Загрузка дизайна
        self.RegWindow = RegWindow()
        self.UspRegWindow = UspRegWindow()
        uic.loadUi('menu.ui', self)
        self.setWindowTitle('Menu')
        self.VhodButton.clicked.connect(self.vhod)
        self.RegButton.clicked.connect(self.registracia)

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
                UserLogin = res[0][0]
                UserPassword = res[0][1]
                UserKeys = res[0][3]
                self.OsnWindow = WeeklyPlannerWindow(UserLogin, UserPassword, UserKeys)
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
    def __init__(self):
        super().__init__()
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
            name = hashlib.sha256(name.encode('utf-8')).hexdigest()
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
    def __init__(self, UserLogin, UserPassword, WeekDays):
        super().__init__()
        uic.loadUi('WeeklyPlannerTheWeek.ui', self)
        self.setWindowTitle('WeeklyPlanner')
        self.SetButton.clicked.connect(self.openSet)
        self.EvrDButton.clicked.connect(self.openEvrydayTasks)
        self.LWButton.clicked.connect(self.LastWeekop)
        self.NWButton.clicked.connect(self.NextWeekop)
        self.fill_dates()
        self.add_week_data()

    def fill_dates(self):
        # Получаем текущий день недели (0 - Понедельник, 6 - Воскресенье)
        today = datetime.today()
        weekday_index = today.weekday()

        # Определяем понедельник текущей недели
        start_of_week = today - timedelta(days=weekday_index)

        # Список виджетов для заполнения (обновите эти имена в соответствии с вашей .ui)
        date_widgets = [
            self.dateMonday,  # Поле для понедельника
            self.dateTuesday,  # Поле для вторника
            self.dateWednesday,  # Поле для среды
            self.dateThursday,  # Поле для четверга
            self.dateFriday,  # Поле для пятницы
            self.dateSaturday,  # Поле для субботы
            self.dateSunday  # Поле для воскресенья
        ]

        # Заполняем каждое поле датой соответствующего дня
        years = set()
        for i, widget in enumerate(date_widgets):
            day_date = start_of_week + timedelta(days=i)
            formatted_date = day_date.strftime('%d.%m')  # Формат день.месяц
            widget.setText(formatted_date)
            years.add(day_date.year)

        year_display = f"{min(years)}-{max(years)}" if len(years) > 1 else str(min(years))
        self.labelYear.setText(f'Год: {year_display}')

    def add_week_data(self):
        pass

    def openSet(self):
        pass

    def openEvrydayTasks(self):
        pass

    def LastWeekop(self):
        pass

    def NextWeekop(self):
        pass


class UspRegWindow(QDialog):
    def __init__(self):
        super().__init__()
        # Загружаем дизайн
        uic.loadUi('UspReg.ui', self)
        self.setWindowTitle('Successful registration')
        self.pushButton.clicked.connect(self.close)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    menu = MainMenu()
    menu.show()
    sys.exit(app.exec())
