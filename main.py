import dataclasses
import json
import sys
import typing
from pathlib import Path

from PyQt5 import QtWidgets as QtW
from PyQt5 import QtGui as QtG
from PyQt5 import QtCore as QtC

from main_window import Ui_MainWindow
from turmites.infinite_grid import Position
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

    def get_color(self, state: StateType) -> QtG.QColor:
        return self.states[state]

    def set_color(self, state: StateType, color: QtG.QColor):
        self.states[state] = color


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

        self.state_colors = state_colors
        self.display(state)

        self.combo_box.currentIndexChanged.connect(update_callback)

    def display(self, target_state: StateColors.StateType = None):
        target_state = target_state if target_state is not None else self.get_current_state()

        self.combo_box.clear()
        for state, color in self.state_colors.states.items():
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
        color = QtW.QColorDialog.getColor()

        if color.isValid():
            self.callback(color)


class TurmitesGraphicsView:
    _scale = 25

    def __init__(self, graphics_view: QtW.QGraphicsView, turmite_model: MultipleTurmiteModel,
                 cell_state_colors: StateColors, turmite_state_colors: list[StateColors]):
        self.turmite_model = turmite_model
        self.cell_state_colors = cell_state_colors
        self.turmite_state_colors = turmite_state_colors

        self.scene = QtW.QGraphicsScene()

        self.view = graphics_view
        self.view.setScene(self.scene)
        self.view.setRenderHints(QtG.QPainter.Antialiasing | QtG.QPainter.SmoothPixmapTransform)
        self.view.setDragMode(QtW.QGraphicsView.ScrollHandDrag)
        self.view.setTransformationAnchor(QtW.QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QtW.QGraphicsView.AnchorUnderMouse)
        self.view.setMouseTracking(True)

        self.view.scale(1, 1)

        # on scroll, zoom in/out
        self.view.wheelEvent = self.on_wheel_event

        self.cell_graphics_items: dict[Position, QtW.QGraphicsItem] = {}
        self.turmite_graphics_items: list[QtW.QGraphicsItem] = []

        self.init_grid()
        self.draw_turmites()
        self.turmite_model.grid.listeners.append(self.update_cell)
        # self.view.eventFilter = self.graphics_view_event_filter

    def update_cell(self, position: Position, cell_state: int):
        x, y = position

        if position in self.cell_graphics_items:
            self.scene.removeItem(self.cell_graphics_items[position])

        if cell_state == self.turmite_model.grid.default:
            return

        self.cell_graphics_items[position] = self.scene.addRect(
            QtC.QRectF(x * self._scale, y * self._scale, self._scale, self._scale),
            QtG.QPen(QtG.QColor(0, 0, 0)),
            QtG.QBrush(self.cell_state_colors.get_color(cell_state))
        )

    def draw_turmites(self):
        for turmite_graphics_item in self.turmite_graphics_items:
            self.scene.removeItem(turmite_graphics_item)

        self.turmite_graphics_items.clear()

        for turmite, state_colors in zip(self.turmite_model.turmites, self.turmite_state_colors):
            x, y = turmite.position
            self.turmite_graphics_items.append(
                self.scene.addEllipse(
                    x * self._scale, y * self._scale, self._scale, self._scale,
                    QtG.QPen(QtG.QColor(0, 0, 0), 1),
                    QtG.QBrush(state_colors.get_color(turmite.state))
                )
            )

    def init_grid(self):
        self.scene.setBackgroundBrush(self.cell_state_colors.get_color(self.turmite_model.grid.default))

        for item in self.cell_graphics_items.values():
            self.scene.removeItem(item)

        self.cell_graphics_items: dict[Position, QtW.QGraphicsItem] = {}

        for position, cell_state in self.turmite_model.grid.items():
            self.update_cell(position, cell_state)

    def on_wheel_event(self, event: QtG.QWheelEvent):
        if event.angleDelta().y() > 0:
            self.view.scale(1.1, 1.1)
        else:
            self.view.scale(0.9, 0.9)
    """
    
    bool MyGraphicsView::eventFilter(QObject *object, QEvent *event) {
     
      if (event->type() == QEvent::MouseButtonPress)
      {
          QMouseEvent* mouse_event = static_cast<QMouseEvent*>(event);
          // Enter here any button you like
          if (mouse_event->button() == Qt::MiddleButton)
          {
              // temporarly enable dragging mode
              this->setDragMode(QGraphicsView::DragMode::ScrollHandDrag);
              // emit a left mouse click (the default button for the drag mode)
              QMouseEvent* pressEvent = new QMouseEvent(QEvent::GraphicsSceneMousePress, 
                                        mouse_event->pos(), Qt::MouseButton::LeftButton,
                                        Qt::MouseButton::LeftButton, Qt::KeyboardModifier::NoModifier);
              
              this->mousePressEvent(pressEvent);
          }
          else if (event->type() == QEvent::MouseButtonRelease)
          {
              // disable drag mode if dragging is finished
              this->setDragMode(QGraphicsView::DragMode::NoDrag);
          }
          
          Q_UNUSED(object)
          return false;
    }"""

    @staticmethod
    def graphics_view_event_filter(self: QtW.QGraphicsView, obj, event: QtC.QEvent):
        if event.type() == QtC.QEvent.MouseButtonPress:
            event: QtG.QMouseEvent

            if event.button() == QtC.Qt.MouseButton.RightButton:
                self.setDragMode(QtW.QGraphicsView.DragMode.ScrollHandDrag)

                press_event = QtG.QMouseEvent(
                    QtC.QEvent.GraphicsSceneMousePress,
                    event.pos(),
                    QtC.Qt.MouseButton.LeftButton,
                    QtC.Qt.KeyboardModifier.NoModifier
                )
                self.mousePressEvent(press_event)

        elif event.type() == QtC.QEvent.MouseButtonRelease:
            ...


class AddListEntryButton(QtW.QWidget):
    def __init__(self, parent, callback):
        super().__init__(parent)

        self.main_layout = QtW.QVBoxLayout()
        self.button = QtW.QPushButton("Add Transition Table Entry")
        self.main_layout.addWidget(self.button)
        self.setLayout(self.main_layout)

        self.callback = callback
        self.button.clicked.connect(callback)


@dataclasses.dataclass
class Project:
    model: MultipleTurmiteModel = dataclasses.field(default_factory=MultipleTurmiteModel)
    cell_state_colors: StateColors = dataclasses.field(default_factory=StateColors)
    turmite_state_colors: list[StateColors] = dataclasses.field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "model": self.model.to_json(),
            "cell_state_colors": self.cell_state_colors.to_json(),
            "turmite_state_colors": [colors.to_json() for colors in self.turmite_state_colors]
        }

    @classmethod
    def from_json(cls, data: dict) -> "Project":
        return cls(
            MultipleTurmiteModel.from_json(data["model"]),
            StateColors.from_json(data["cell_state_colors"]),
            [StateColors.from_json(colors) for colors in data["turmite_state_colors"]]
        )


class StateWidget(QtW.QWidget):
    def __init__(self, state: int, state_colors: StateColors, delete_callback, change_callback):
        super().__init__()

        self.state = state
        self.state_colors = state_colors
        self.delete_callback = delete_callback
        self.change_callback = change_callback
        self.display()

    def contextMenuEvent(self, event: QtG.QContextMenuEvent) -> None:
        menu = QtW.QMenu()
        change_action = menu.addAction("Change Color")
        delete_action = menu.addAction("Delete")

        delete_action.triggered.connect(self.delete_callback)
        change_action.triggered.connect(self.on_change)

        menu.exec_(self.mapToGlobal(event.pos()))

    def on_change(self):
        color = QtW.QColorDialog.getColor()

        if color.isValid():
            self.change_callback(self.state, color)

    def display(self):
        main_layout = QtW.QHBoxLayout()
        label = QtW.QLabel(str(self.state))
        # set label background to white
        label.setStyleSheet("background-color: white")

        pm = get_pixmap(self.state_colors.get_color(self.state))
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

        self.tick_timer = QtC.QTimer()
        self.tick_timer.timeout.connect(self.tick)
        self.tick_timer.setInterval(int(1 / 60 * 1000))

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

    def draw_add_transition_table_entry(self):
        row = self.ui.transitionTableTableWidget.rowCount()
        self.ui.transitionTableTableWidget.insertRow(row)

        self.ui.transitionTableTableWidget.setCellWidget(row, 0, AddListEntryButton(self.ui.transitionTableTableWidget,
                                                                                    self.add_transition_table_entry))

    def add_transition_table_entry(self):
        self.current_turmite().transition_table

        self.update_transition_table()

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

    def draw_turmites_combo_box(self):
        self.ui.selectedTurmiteComboBox.clear()

        for i, turmite in enumerate(self.project.model.turmites):
            self.ui.selectedTurmiteComboBox.addItem(f"Turmite #{i + 1}")

        self.ui.selectedTurmiteComboBox.currentIndexChanged.connect(self.draw_turmite_specific)

    def draw_state_table(self, table: QtW.QTableWidget, state_colors: StateColors, msg: str):
        # palette = table.palette()
        # palette.setBrush(QtG.QPalette.Base, QtG.QBrush(QtG.QColor(0, 0, 0), Qt.BDiagPattern))
        # table.setPalette(palette)

        table.clear()
        table.setRowCount(1)
        table.setColumnCount(len(state_colors.states) + 1)

        col = -1
        for col, state in enumerate(state_colors.states):
            table.setCellWidget(
                0, col,
                StateWidget(
                    state, state_colors,
                    lambda *_, __i=col: self.remove_state_color(table, state_colors, __i, msg),
                    lambda state, color: self.set_state_color(table, state_colors, state, color, msg)
                )
            )

        def add_color_callback(color: QtG.QColor):
            new_state = state_colors.next_free_state()
            self.set_state_color(table, state_colors, new_state, color, msg)

        add_state_widget = AddStateButton(table, msg, add_color_callback)
        table.setCellWidget(0, col + 1, add_state_widget)

        self.setup_state_table(table)

    def set_state_color(self, table: QtW.QTableWidget, state_colors: StateColors, state: StateColors.StateType,
                        color: QtG.QColor, msg: str):
        state_colors.set_color(state, color)
        self.draw_state_table(table, state_colors, msg)
        self.draw_transition_table()

        self.turmites_view.init_grid()
        self.turmites_view.draw_turmites()

    def remove_state_color(self, table: QtW.QTableWidget, state_colors: StateColors, index: int, msg: str) -> None:
        key = list(state_colors.states.keys())[index]

        del state_colors.states[key]
        self.draw_state_table(table, state_colors, msg)
        self.draw_transition_table()

        self.turmites_view.init_grid()
        self.turmites_view.draw_turmites()

    @staticmethod
    def setup_state_table(table: QtW.QTableWidget):
        table.verticalHeader().setSectionResizeMode(QtW.QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(QtW.QHeaderView.ResizeToContents)

        table.setVerticalScrollBarPolicy(QtC.Qt.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(QtC.Qt.ScrollBarAlwaysOn)

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

        self.turmites_view = TurmitesGraphicsView(
            self.ui.simulationView,
            self.project.model,
            self.project.cell_state_colors,
            self.project.turmite_state_colors
        )

        self.ui.playToolButton.clicked.connect(self.start_simulation)
        self.ui.actionPlay.triggered.connect(self.start_simulation)
        self.ui.fullStepToolButton.clicked.connect(self.full_step)
        self.ui.actionFullStep.triggered.connect(self.full_step)
        self.ui.stepOneTurmiteToolButton.clicked.connect(self.step_one_turmite)
        self.ui.actionStepOneTurmite.triggered.connect(self.step_one_turmite)

    def save_project(self):
        file_path, *_ = QtW.QFileDialog.getSaveFileName(self.ui.centralwidget, "Save Project", "", "JSON (*.json)")

        if not file_path:
            return

        file_path = Path(file_path).with_suffix(".json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.project.to_json(), f, indent=2)

    def draw_turmite_specific(self):
        self.draw_transition_table()
        self.draw_state_table(self.ui.turmiteStatesTableWidget, self.current_turmite_colors(), "Add Turmite State")

    def start_simulation(self):
        self.ui.playToolButton.clicked.connect(self.stop_simulation)
        self.ui.playToolButton.clicked.disconnect(self.start_simulation)
        self.ui.actionPlay.triggered.connect(self.stop_simulation)
        self.ui.actionPlay.triggered.disconnect(self.start_simulation)
        self.tick_timer.start()
        self.ui.playToolButton.setText("Stop")
        self.ui.actionPlay.setText("Stop")

    def stop_simulation(self):
        self.ui.playToolButton.clicked.connect(self.start_simulation)
        self.ui.playToolButton.clicked.disconnect(self.stop_simulation)
        self.ui.actionPlay.triggered.connect(self.start_simulation)
        self.ui.actionPlay.triggered.disconnect(self.stop_simulation)
        self.tick_timer.stop()
        self.ui.playToolButton.setText("Start")
        self.ui.actionPlay.setText("Start")

    def tick(self):
        for _ in range(self.ui.speedSpinBox.value()):
            self.project.model.step()

        self.turmites_view.draw_turmites()

    def step_one_turmite(self):
        self.project.model.step_small()
        self.turmites_view.draw_turmites()

    def full_step(self):
        self.project.model.step()
        self.turmites_view.draw_turmites()


class MainWindow(QtW.QMainWindow, Ui_MainWindow):
    def __init__(self, project: Project = None):
        super().__init__()
        self.setupUi(self)

        project = Project() if project is None else project
        self.set_project(project)

        self.actionOpen.triggered.connect(self.open_project)
        self.actionQuit.triggered.connect(self.close)

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

    def closeEvent(self, close_event: QtG.QCloseEvent) -> None:
        msg_box = QtW.QMessageBox()
        msg_box.setIcon(QtW.QMessageBox.Warning)
        msg_box.setWindowTitle("Quit")
        msg_box.setText("All unsaved changes will be lost.")
        msg_box.setStandardButtons(QtW.QMessageBox.Ok | QtW.QMessageBox.Cancel)

        if msg_box.exec() == QtW.QMessageBox.Ok:
            close_event.accept()
        else:
            close_event.ignore()


def main(args: list[str]):
    with open("test_project_langtons_ant.json", "r", encoding="utf-8") as f:
        test_proj = Project.from_json(json.load(f))

    app = QtW.QApplication(args)
    window = MainWindow(test_proj)
    window.show()
    app.exec_()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
