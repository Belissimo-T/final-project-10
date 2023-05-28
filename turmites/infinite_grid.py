from __future__ import annotations

import typing

Position = typing.Tuple[int, int]

T = typing.TypeVar("T")


class InfiniteGrid(typing.Generic[T]):
    def __init__(self, default: T, _grid: dict[Position, T] = None):
        self._grid: dict[Position, T] = {} if _grid is None else _grid
        self.default = default
        self.listeners: list[typing.Callable[[Position, T], None]] = []

    def _call_listeners(self, key: Position, value: T):
        for grid_listener in self.listeners:
            grid_listener(key, value)

    def __setitem__(self, key: Position, value: T):
        if value == self.default:
            self._grid.pop(key, None)
        else:
            self._grid[key] = value

        self._call_listeners(key, value)

    def __getitem__(self, item: Position):
        return self._grid.get(item, self.default)

    def __len__(self):
        return len(self._grid)

    def items(self):
        for key, value in self._grid.items():
            yield key, value

    def to_json(self) -> dict:
        return {
            "grid": [[";".join(map(str, key)), value] for key, value in self._grid.items()],
            "default": self.default
        }

    def clear(self):
        for key in list(self._grid.keys()):
            self[key] = self.default

    @classmethod
    def from_json(cls, data: dict) -> "InfiniteGrid":
        # noinspection PyTypeChecker
        return cls(
            data["default"],
            dict(
                (tuple(map(lambda x: int(float(x)), key.split(";"))), value)
                for key, value in data["grid"]
            )
        )
