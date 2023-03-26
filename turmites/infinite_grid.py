from __future__ import annotations

import typing

Position = typing.Tuple[int, int]

T = typing.TypeVar("T")


class InfiniteGrid(typing.Generic[T]):
    def __init__(self, default: T, _grid: dict[Position, T] = None):
        self._grid: dict[Position, T] = {} if _grid is None else _grid
        self._default = default
        self._grid_listeners: typing.Iterable[typing.Callable[[Position, T], None]] = []

    def _call_grid_listeners(self, key: Position, value: T):
        for grid_listener in self._grid_listeners:
            grid_listener(key, value)

    def __setitem__(self, key: Position, value: T):
        if value == self._default:
            self._grid.pop(key)
        else:
            self._grid[key] = value

        self._call_grid_listeners(key, value)

    def __getitem__(self, item: Position):
        return self._grid.get(item, self._default)

    def __len__(self):
        return len(self._grid)

    def to_json(self) -> dict:
        return {
            "grid": [[";".join(map(str, key)), value] for key, value in self._grid.items()],
            "default": self._default
        }

    @classmethod
    def from_json(cls, data: dict) -> "InfiniteGrid":
        return cls(
            data["default"],
            dict(
                (tuple(map(int, key.split(";"))), value)
                for key, value in data["grid"]
            )
        )
