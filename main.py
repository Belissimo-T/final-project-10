import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

from main_window import Ui_MainWindow


class StateWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.mainLayout = QVBoxLayout(self)
        # # # self.setFixedSize(100,100)
        # self.mainLayout.addWidget(QComboBox())
        # self.setLayout(self.mainLayout)

        self.allQHBoxLayout = QHBoxLayout()
        self.iconQLabel = QLabel()
        self.allQHBoxLayout.addWidget(self.iconQLabel, 0)
        self.setLayout(self.allQHBoxLayout)


class AddStateWidget(QWidget):
    def __init__(self, parent, msg: str):
        super().__init__(parent)

        self.mainLayout = QVBoxLayout()
        self.button = QPushButton(msg)
        self.mainLayout.addWidget(self.button)
        self.setLayout(self.mainLayout)


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setup_state_table(self.cellStatesTableWidget, "Add a cell state")
        self.setup_state_table(self.turmiteStatesTableWidget, "Add a turmite state")

        # self.transitionTableTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.transitionTableTableWidget.resizeColumnsToContents()
        self.transitionTableTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

    @staticmethod
    def setup_state_table(table: QTableWidget, msg: str):
        custom_widget = AddStateWidget(table, msg)

        table.setRowCount(1)
        table.setColumnCount(1)
        table.setCellWidget(0, 0, custom_widget)

        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        table.setFixedHeight(
            table.verticalHeader().length()
            + table.horizontalHeader().height()
            + table.horizontalScrollBar().height()
        )


def main(args: list[str]):
    app = QApplication(args)
    window = MainWindow()
    window.show()
    app.exec_()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
