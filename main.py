import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QStyleFactory

from main_window import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


def main(args: list[str]):
    app = QApplication(args)
    print(QStyleFactory.keys())
    window = MainWindow()
    window.show()
    app.exec_()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
