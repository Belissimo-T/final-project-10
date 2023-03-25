import dataclasses
import typing

from .infinite_grid import InfiniteGrid, Pos

TurmiteDirection = typing.Literal[0, 1, 2, 3]
TurmiteTurnDirection = int
CellColor = int
TurmiteState = int


class UnknownStateError(Exception):
    """Error that gets raised if there is no entry in the transition table for the given state."""


class TransitionTable:
    def __init__(self):
        self._transition_dict: dict[
            tuple[CellColor, TurmiteState],
            tuple[TurmiteTurnDirection, CellColor, TurmiteState]
        ] = {}

    def get_entry(self,
                  cell_color: CellColor,
                  turmite_state: TurmiteState
                  ) -> tuple[TurmiteTurnDirection, CellColor, TurmiteState]:
        try:
            return self._transition_dict[cell_color, turmite_state]
        except KeyError as e:
            raise UnknownStateError from e


@dataclasses.dataclass
class Turmite:
    transition_table: TransitionTable

    # position
    pos: Pos

    direction: TurmiteDirection
    state: TurmiteState

    def step(self, cell_color: CellColor) -> CellColor:
        turn_direction, new_cell_color, self.state = self.transition_table.get_entry(cell_color, self.state)

        self.direction += turn_direction
        self.direction %= 4

        self._go_forward()

        return new_cell_color

    def _go_forward(self):
        x, y = self.pos

        if self.direction == 0:
            y += 1  # up
        elif self.direction == 1:
            x -= 1  # left
        elif self.direction == 2:
            y -= 1  # down
        elif self.direction == 3:
            x += 1  # right

        self.pos = x, y


class MultipleTurmiteModel:
    def __init__(self, turmites: list[Turmite]):
        self.turmites = turmites
        self.grid = InfiniteGrid[CellColor](default=0)
        self.small_step = 0

    def step_small(self):
        curr_turmite = self.turmites.pop(0)

        turmite_pos = curr_turmite.pos
        new_color = curr_turmite.step(self.grid[turmite_pos])
        self.grid[turmite_pos] = new_color

        self.turmites.append(curr_turmite)
        self.small_step += 1
        self.small_step %= len(self.turmites)

    def step(self):
        for _ in range(len(self.turmites)):
            self.step_small()
