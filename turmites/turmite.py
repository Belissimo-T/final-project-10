from __future__ import annotations

import dataclasses
import math
import typing

from .infinite_grid import InfiniteGrid, Position

TurmiteDirection = typing.Literal[0, 1, 2, 3]
TurmiteTurnDirection = int
CellColor = int
TurmiteState = int


class UnknownStateError(Exception):
    """Error that gets raised if there is no entry in the transition table for the given state."""


class TransitionTable:
    _TransitionDictType = typing.Dict[
        typing.Tuple[CellColor, TurmiteState],
        typing.Tuple[TurmiteTurnDirection, CellColor, TurmiteState]
    ]

    def __init__(self, _transition_dict: _TransitionDictType = None):
        self._transition_dict: TransitionTable._TransitionDictType = (
            {} if _transition_dict is None else _transition_dict
        )

    def get_entry(self,
                  cell_color: CellColor,
                  turmite_state: TurmiteState
                  ) -> tuple[TurmiteTurnDirection, CellColor, TurmiteState]:
        try:
            return self._transition_dict[cell_color, turmite_state]
        except KeyError as e:
            raise UnknownStateError from e

    def set_entry(self,
                  cell_color: CellColor,
                  turmite_state: TurmiteState,
                  turn_direction: TurmiteTurnDirection,
                  new_cell_color: CellColor,
                  new_turmite_state: TurmiteState
                  ):
        self._transition_dict[cell_color, turmite_state] = (
            turn_direction, new_cell_color, new_turmite_state
        )

    def clear(self):
        self._transition_dict.clear()

    def invert_direction(self) -> TransitionTable:
        return TransitionTable({key: (-value[0], value[1], value[2]) for key, value in self._transition_dict.items()})

    def __contains__(self, item: tuple[CellColor, TurmiteState]) -> bool:
        return item in self._transition_dict

    def __iter__(self):
        return iter(self._transition_dict.items())

    def __len__(self):
        return len(self._transition_dict)

    def to_json(self) -> list:
        return list(self._transition_dict.items())

    @classmethod
    def from_json(cls, data: list) -> "TransitionTable":
        return cls({tuple(key): tuple(value) for key, value in data})


def direction_to_xy_diff(direction: TurmiteDirection) -> tuple[int, int]:
    return {
        0: (0, 1),  # down
        1: (-1, 0),  # left
        2: (0, -1),  # up
        3: (1, 0)  # right
    }[direction]


@dataclasses.dataclass
class Turmite:
    transition_table: TransitionTable

    position: Position = (0, 0)

    direction: TurmiteDirection = 0
    state: TurmiteState = 0

    def step(self, cell_color: CellColor) -> CellColor:
        turn_direction, new_cell_color, self.state = self.transition_table.get_entry(cell_color, self.state)

        self.direction += turn_direction
        self.direction %= 4

        self._go_forward()

        return new_cell_color

    def _go_forward(self):
        x, y = self.position

        dx, dy = direction_to_xy_diff(self.direction)

        self.position = x + dx, y + dy

    def to_json(self) -> dict:
        return {
            "transition_table": self.transition_table.to_json(),
            "position": self.position,
            "direction": self.direction,
            "state": self.state
        }

    @classmethod
    def from_json(cls, data: dict) -> "Turmite":
        return cls(
            TransitionTable.from_json(data["transition_table"]),
            tuple(data["position"]),
            data["direction"],
            data["state"]
        )


class MultipleTurmiteModel:
    def __init__(self, turmites: list[Turmite] = None, grid: InfiniteGrid[CellColor] = None, _small_step: int = 0):
        self.turmites = [] if turmites is None else turmites
        self.grid = InfiniteGrid[CellColor](default=0) if grid is None else grid
        self.small_step = _small_step
        self.iteration: int = 0

    def step_small(self):
        curr_turmite = self.turmites[self.small_step]

        turmite_pos = curr_turmite.position
        new_color = curr_turmite.step(self.grid[turmite_pos])
        self.grid[turmite_pos] = new_color

        self.small_step += 1
        if self.small_step >= len(self.turmites):
            self.iteration += 1
        self.small_step %= len(self.turmites)

    def step(self):
        for _ in range(len(self.turmites)):
            self.step_small()

    def to_json(self) -> dict:
        return {
            "turmites": [turmite.to_json() for turmite in self.turmites],
            "grid": self.grid.to_json(),
            "small_step": self.small_step
        }

    @classmethod
    def from_json(cls, data: dict) -> "MultipleTurmiteModel":
        return cls(
            [Turmite.from_json(turmite_json) for turmite_json in data["turmites"]],
            InfiniteGrid.from_json(data["grid"]),
            data["small_step"]
        )
