import dataclasses
import json
import sys
import typing

from PyQt5 import QtWidgets as QtW
from PyQt5 import QtGui as QtG
from PyQt5.QtCore import Qt

from main_window import Ui_MainWindow
from turmites.turmite import TransitionTable, MultipleTurmiteModel, TurmiteState, CellColor


class StateColorManager:
    StateType = typing.Union[TurmiteState, CellColor]

    def __init__(self, states: dict["TurmiteState | CellColor", QtG.QColor] = None):
        self.states: dict[StateColorManager.StateType, QtG.QColor] = {} if states is None else states
        self.subscribers: list[StateComboBox] = []

    def to_json(self) -> dict:
        return {str(state): color.rgb() for state, color in self.states.items()}

    @classmethod
    def from_json(cls, data: dict) -> "StateColorManager":
        return cls({int(state): QtG.QColor(color) for state, color in data.items()})

    def subscribe(self, subscriber: "StateComboBox"):
        self.subscribers.append(subscriber)

    def notify_subscribers(self):
        for subscriber in self.subscribers:
            subscriber.display()


class StateComboBox(QtW.QWidget):
    def __init__(self, state: StateColorManager.StateType, state_mgr: StateColorManager):
        super().__init__()

        self.mainLayout = QtW.QVBoxLayout()
        self.combo_box = QtW.QComboBox()
        self.mainLayout.addWidget(self.combo_box)
        self.setLayout(self.mainLayout)

        self.state_mgr = state_mgr
        self.state_mgr.subscribe(self)
        self.display(state)

    def display(self, target_state: StateColorManager.StateType = None):
        target_state = target_state if target_state is not None else self.get_current_state()

        self.combo_box.clear()
        for state, color in self.state_mgr.states.items():
            pixmap = QtG.QPixmap(100, 100)
            pixmap.fill(color)
            icon = QtG.QIcon(pixmap)
            self.combo_box.addItem(icon, str(state), state)

        self.combo_box.setCurrentIndex(self.combo_box.findData(target_state))

    def get_current_state(self) -> StateColorManager.StateType:
        return self.combo_box.currentData()


class AddStateButton(QtW.QWidget):
    def __init__(self, parent, msg: str):
        super().__init__(parent)

        self.mainLayout = QtW.QVBoxLayout()
        self.button = QtW.QPushButton(msg)
        self.mainLayout.addWidget(self.button)
        self.setLayout(self.mainLayout)


@dataclasses.dataclass
class Project:
    model: MultipleTurmiteModel = dataclasses.field(default_factory=MultipleTurmiteModel)
    cell_states_mgr: StateColorManager = dataclasses.field(default_factory=StateColorManager)
    turmite_states_mgrs: list[StateColorManager] = dataclasses.field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "model": self.model.to_json(),
            "cell_states": self.cell_states_mgr.to_json(),
            "turmite_states": [mgr.to_json() for mgr in self.turmite_states_mgrs]
        }

    @classmethod
    def from_json(cls, data: dict) -> "Project":
        return cls(
            MultipleTurmiteModel.from_json(data["model"]),
            StateColorManager.from_json(data["cell_states"]),
            [StateColorManager.from_json(mgr) for mgr in data["turmite_states"]]
        )


class ProjectView:
    def __init__(self, project: Project, ui: Ui_MainWindow):
        self.project = project
        self.ui = ui

    def draw_transition_table(self, turmite_index: int):
        turmite = self.project.model.turmites[turmite_index]
        state_mgr = self.project.turmite_states_mgrs[turmite_index]

        self.ui.transitionTableTableWidget.setRowCount(len(turmite.transition_table))

        for row, (key, value) in enumerate(turmite.transition_table):
            (cell_color, turmite_state) = key
            (turn_direction, new_cell_color, new_turmite_state) = value
            self.ui.transitionTableTableWidget.setCellWidget(row, 0,
                                                             StateComboBox(cell_color, self.project.cell_states_mgr))
            self.ui.transitionTableTableWidget.setCellWidget(row, 1, StateComboBox(turmite_state, state_mgr))
            self.ui.transitionTableTableWidget.setCellWidget(row, 2, QtW.QLabel(str(turn_direction)))
            self.ui.transitionTableTableWidget.setCellWidget(row, 3, StateComboBox(new_cell_color,
                                                                                   self.project.cell_states_mgr))
            self.ui.transitionTableTableWidget.setCellWidget(row, 4, StateComboBox(new_turmite_state, state_mgr))

        self.draw_add_transition_table_entry()

    def draw_add_transition_table_entry(self):
        row = self.ui.transitionTableTableWidget.rowCount()
        self.ui.transitionTableTableWidget.insertRow(row)
        self.ui.transitionTableTableWidget.setCellWidget(row, 0, QtW.QLabel("Add new entry"))
        self.ui.transitionTableTableWidget.setCellWidget(row, 1, QtW.QLabel("Add"))
        self.ui.transitionTableTableWidget.setCellWidget(row, 2, QtW.QLabel("Add"))
        self.ui.transitionTableTableWidget.setCellWidget(row, 3, QtW.QLabel("Add"))
        self.ui.transitionTableTableWidget.setCellWidget(row, 4, QtW.QLabel("Add"))
        self.ui.transitionTableTableWidget.setCellWidget(row, 5, QtW.QLabel("Add"))
        self.ui.transitionTableTableWidget.resizeRowsToContents()

    def draw_turmites_list(self):
        self.ui.selectedTurmiteComboBox.clear()

        for i, turmite in enumerate(self.project.model.turmites):
            self.ui.selectedTurmiteComboBox.addItem(f"Turmite #{i + 1}")

    def draw_state_table(self, table: QtW.QTableWidget, state_mgr: StateColorManager, msg: str):
        table.setRowCount(1)
        table.setColumnCount(len(state_mgr.states) + 1)

        col = 0
        for col, state in enumerate(state_mgr.states):
            table.setCellWidget(0, col, StateComboBox(state, state_mgr))

        add_state_widget = AddStateButton(table, msg)
        table.setCellWidget(0, col + 1, add_state_widget)

        self.setup_state_table(table)

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

        self.draw_state_table(self.ui.cellStatesTableWidget, self.project.cell_states_mgr, "Add Cell State")
        # self.draw_state_table(self.ui.turmiteStatesTableWidget, "Add Turmite State")
        self.draw_transition_table(0)
        self.draw_turmites_list()


class MainWindow(QtW.QMainWindow, Ui_MainWindow):

    def __init__(self, project: Project = None):
        super().__init__()
        self.setupUi(self)

        project = Project() if project is None else project
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
