import dataclasses
import json
import sys
import typing
from pathlib import Path

from PyQt5 import QtWidgets as QtW
from PyQt5 import QtGui as QtG
from PyQt5.QtCore import Qt

from main_window import Ui_MainWindow
from turmites.turmite import MultipleTurmiteModel, TurmiteState, CellColor


class StateColors:
    StateType = typing.Union[TurmiteState, CellColor]

    def __init__(self, states: dict["TurmiteState | CellColor", QtG.QColor] = None):
        self.states: dict[StateColors.StateType, QtG.QColor] = {} if states is None else states

    def next_free_state(self) -> StateType:
        for i in range(len(self.states)):
            if i not in self.states:
                return i

        return len(self.states)

    def to_json(self) -> dict:
        return {str(state): color.rgb() for state, color in self.states.items()}

    @classmethod
    def from_json(cls, data: dict) -> "StateColors":
        return cls({int(state): QtG.QColor(color) for state, color in data.items()})


def get_pixmap(color: QtG.QColor):
    pixmap = QtG.QPixmap(16, 16)
    pixmap.fill(color)

    return pixmap


def get_icon(color: QtG.QColor):
    pixmap = get_pixmap(color)

    icon = QtG.QIcon(pixmap)

    return icon


class StateComboBox(QtW.QWidget):
    def __init__(self, state: StateColors.StateType, state_colors: StateColors, update_callback):
        super().__init__()

        self.main_layout = QtW.QVBoxLayout()
        self.combo_box = QtW.QComboBox()
        self.main_layout.addWidget(self.combo_box)
        self.setLayout(self.main_layout)

        self.state_mgr = state_colors
        self.display(state)

        self.combo_box.currentIndexChanged.connect(update_callback)

    def display(self, target_state: StateColors.StateType = None):
        target_state = target_state if target_state is not None else self.get_current_state()

        self.combo_box.clear()
        for state, color in self.state_mgr.states.items():
            icon = get_icon(color)
            self.combo_box.addItem(icon, str(state), state)

        self.combo_box.setCurrentIndex(self.combo_box.findData(target_state))

    def get_current_state(self) -> StateColors.StateType:
        return self.combo_box.currentData()


class TurnDirectionComboBox(QtW.QWidget):
    TURN_DIRECTIONS = {
        0: "Don't turn",
        1: "Turn left",
        2: "Turn around",
        3: "Turn right",
    }

    def __init__(self, turn_direction: int, update_callback):
        super().__init__()

        self.main_layout = QtW.QHBoxLayout()
        self.combo_box = QtW.QComboBox()
        self.main_layout.addWidget(self.combo_box)
        self.setLayout(self.main_layout)

        for direction, msg in self.TURN_DIRECTIONS.items():
            self.combo_box.addItem(msg, direction)

        self.combo_box.setCurrentIndex(self.combo_box.findData(turn_direction % 4))

        self.combo_box.currentIndexChanged.connect(update_callback)

    def get_current_turn_direction(self) -> int:
        return self.combo_box.currentData()


class AddStateButton(QtW.QWidget):
    def __init__(self, parent, msg: str, callback):
        super().__init__(parent)

        self.main_layout = QtW.QVBoxLayout()
        self.button = QtW.QPushButton(msg)
        self.main_layout.addWidget(self.button)
        self.setLayout(self.main_layout)

        self.callback = callback
        self.button.clicked.connect(self.on_clicked)

    def on_clicked(self):
        # open colorchooser
        color = QtW.QColorDialog.getColor()

        if color.isValid():
            self.callback(color)


@dataclasses.dataclass
class Project:
    model: MultipleTurmiteModel = dataclasses.field(default_factory=MultipleTurmiteModel)
    cell_state_colors: StateColors = dataclasses.field(default_factory=StateColors)
    turmite_state_colors: list[StateColors] = dataclasses.field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "model": self.model.to_json(),
            "cell_state_colors": self.cell_state_colors.to_json(),
            "turmite_state_colors": [mgr.to_json() for mgr in self.turmite_state_colors]
        }

    @classmethod
    def from_json(cls, data: dict) -> "Project":
        return cls(
            MultipleTurmiteModel.from_json(data["model"]),
            StateColors.from_json(data["cell_state_colors"]),
            [StateColors.from_json(mgr) for mgr in data["turmite_state_colors"]]
        )


class StateWidget(QtW.QWidget):
    def __init__(self, state: int, mgr: StateColors):
        super().__init__()

        self.state = state
        self.mgr = mgr
        self.display()

    def display(self):
        main_layout = QtW.QHBoxLayout()
        label = QtW.QLabel(str(self.state))
        # set label background to white
        label.setStyleSheet("background-color: white")

        pm = get_pixmap(self.mgr.states[self.state])
        color_label = QtW.QLabel()
        color_label.setPixmap(pm)
        color_label.setSizePolicy(QtW.QSizePolicy(QtW.QSizePolicy.Maximum, QtW.QSizePolicy.Maximum))
        color_label.setStyleSheet("border: 1px solid black;")

        main_layout.addWidget(color_label)
        main_layout.addWidget(label)
        self.setLayout(main_layout)


class ProjectView:
    def __init__(self, project: Project, ui: Ui_MainWindow):
        self.project = project
        self.ui = ui

    def draw_transition_table(self):
        table = self.ui.transitionTableTableWidget

        turmite = self.current_turmite()
        state_colors = self.current_turmite_colors()

        table.setRowCount(len(turmite.transition_table))

        for row, (key, value) in enumerate(turmite.transition_table):
            cell_color, turmite_state = key
            turn_direction, new_cell_color, new_turmite_state = value

            update_callback = lambda *_: self.update_transition_table()

            table.setCellWidget(row, 0, StateComboBox(cell_color, self.project.cell_state_colors, update_callback))
            table.setCellWidget(row, 1, StateComboBox(turmite_state, state_colors, update_callback))
            table.setCellWidget(row, 2, TurnDirectionComboBox(turn_direction, update_callback))
            table.setCellWidget(row, 3, StateComboBox(new_cell_color, self.project.cell_state_colors, update_callback))
            table.setCellWidget(row, 4, StateComboBox(new_turmite_state, state_colors, update_callback))

        self.draw_add_transition_table_entry()

        table.resizeRowsToContents()
        table.resizeColumnsToContents()

    def current_turmite(self):
        return self.project.model.turmites[self.ui.selectedTurmiteComboBox.currentIndex()]

    def current_turmite_colors(self):
        return self.project.turmite_state_colors[self.ui.selectedTurmiteComboBox.currentIndex()]

    def update_transition_table(self):
        # iterate over all rows in the self.ui.transitionTableTableWidget
        # get the current state of the QComboBoxes
        # update the transition table

        table = self.ui.transitionTableTableWidget

        self.current_turmite().transition_table.clear()
        for row in range(self.ui.transitionTableTableWidget.rowCount()):
            if table.cellWidget(row, 4) is None:
                continue
            cell_color = table.cellWidget(row, 0).get_current_state()
            turmite_state = table.cellWidget(row, 1).get_current_state()
            turn_direction = table.cellWidget(row, 2).get_current_turn_direction()
            new_cell_color = table.cellWidget(row, 3).get_current_state()
            new_turmite_state = table.cellWidget(row, 4).get_current_state()

            self.current_turmite().transition_table.set_entry(
                cell_color, turmite_state,
                turn_direction, new_cell_color, new_turmite_state
            )

    def draw_add_transition_table_entry(self):
        row = self.ui.transitionTableTableWidget.rowCount()
        self.ui.transitionTableTableWidget.insertRow(row)
        self.ui.transitionTableTableWidget.setCellWidget(row, 0, QtW.QLabel("Add new entry"))
        # self.ui.transitionTableTableWidget.setCellWidget(row, 1, QtW.QLabel("Add"))
        # self.ui.transitionTableTableWidget.setCellWidget(row, 2, QtW.QLabel("Add"))
        # self.ui.transitionTableTableWidget.setCellWidget(row, 3, QtW.QLabel("Add"))
        # self.ui.transitionTableTableWidget.setCellWidget(row, 4, QtW.QLabel("Add"))
        # self.ui.transitionTableTableWidget.setCellWidget(row, 5, QtW.QLabel("Add"))

    def draw_turmites_combo_box(self):
        self.ui.selectedTurmiteComboBox.clear()

        for i, turmite in enumerate(self.project.model.turmites):
            self.ui.selectedTurmiteComboBox.addItem(f"Turmite #{i + 1}")

        self.ui.selectedTurmiteComboBox.currentIndexChanged.connect(self.draw_turmite_specific)

    def draw_state_table(self, table: QtW.QTableWidget, state_colors: StateColors, msg: str):
        # palette = table.palette()
        # palette.setBrush(QtG.QPalette.Base, QtG.QBrush(QtG.QColor(0, 0, 0), Qt.BDiagPattern))
        # table.setPalette(palette)

        table.setRowCount(1)
        table.setColumnCount(len(state_colors.states) + 1)

        col = 0
        for col, state in enumerate(state_colors.states):
            table.setCellWidget(0, col, StateWidget(state, state_colors))

        def callback(color: QtG.QColor):
            new_state = state_colors.next_free_state()
            self.set_state_color(table, state_colors, new_state, color, msg)

        add_state_widget = AddStateButton(table, msg, callback)
        table.setCellWidget(0, col + 1, add_state_widget)

        self.setup_state_table(table)

    def set_state_color(self, table: QtW.QTableWidget, state_colors: StateColors, state: StateColors.StateType,
                        color: QtG.QColor, msg: str):
        state_colors.states[state] = color
        self.draw_state_table(table, state_colors, msg)

    @staticmethod
    def setup_state_table(table: QtW.QTableWidget):
        table.verticalHeader().setSectionResizeMode(QtW.QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(QtW.QHeaderView.ResizeToContents)

        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        table.setFixedHeight(
            table.verticalHeader().length()
            + table.horizontalHeader().height()
            + table.horizontalScrollBar().height()
        )

    def init(self):
        self.ui.transitionTableTableWidget.resizeColumnsToContents()
        self.ui.transitionTableTableWidget.horizontalHeader().setSectionResizeMode(
            QtW.QHeaderView.ResizeMode.Interactive
        )

        self.draw_state_table(self.ui.cellStatesTableWidget, self.project.cell_state_colors, "Add Cell State")
        self.draw_turmites_combo_box()

        self.draw_turmite_specific()

        self.ui.actionSaveProject.triggered.connect(self.save_project)

    def save_project(self):
        # open qt file dialog with default suffix .json

        file_path, *_ = QtW.QFileDialog.getSaveFileName(self.ui.centralwidget, "Save Project", "", "JSON (*.json)")

        if not file_path:
            return

        file_path = Path(file_path).with_suffix(".json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.project.to_json(), f, indent=2)

    def draw_turmite_specific(self):
        self.draw_transition_table()
        self.draw_state_table(self.ui.turmiteStatesTableWidget, self.current_turmite_colors(), "Add Turmite State")


class MainWindow(QtW.QMainWindow, Ui_MainWindow):

    def __init__(self, project: Project = None):
        super().__init__()
        self.setupUi(self)

        project = Project() if project is None else project
        self.set_project(project)

        self.actionOpen.triggered.connect(self.open_project)

    def open_project(self):
        file_path, *_ = QtW.QFileDialog.getOpenFileName(self, "Open Project", "", "JSON (*.json)")

        if not file_path:
            return

        with open(file_path, "r", encoding="utf-8") as f:
            project = Project.from_json(json.load(f))

        self.set_project(project)

    def set_project(self, project: Project):
        self.project_view = ProjectView(project, self)
        self.project_view.init()


def main(args: list[str]):
    with open("test_project.json", "r", encoding="utf-8") as f:
        test_proj = Project.from_json(json.load(f))

    app = QtW.QApplication(args)
    window = MainWindow(test_proj)
    # window.draw_transition_table(test_model.turmites[0].transition_table)
    window.show()
    app.exec_()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
