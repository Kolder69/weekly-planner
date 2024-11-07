import sys


from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog


class MainMenu(QMainWindow):
    def __init__(self):
        super().__init__()
        # Загрузка дизайна
        uic.loadUi('menu.ui', self)
        self.setWindowTitle('Menu')
        self.VhodButton.clicked.connect(self.vhod)
        self.RegButton.clicked.connect(self.registracia)

    def vhod(self):
        pass

    def registracia(self):
        pass






if __name__ == '__main__':
    app = QApplication(sys.argv)
    menu = MainMenu()
    menu.show()
    sys.exit(app.exec())