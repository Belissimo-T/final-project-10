import typing

Pos = typing.Tuple[int, int]

T = typing.TypeVar("T")


class InfiniteGrid(typing.Generic[T]):
    def __init__(self, default: T):
        self._grid: dict[tuple[int, int], T] = {}
        self._default = default
        self._grid_listeners: typing.Iterable[typing.Callable[[Pos, T], None]] = []

    def _call_grid_listeners(self, key: Pos, value: T):
        for grid_listener in self._grid_listeners:
            grid_listener(key, value)

    def __setitem__(self, key: Pos, value: T):
        if value == self._default:
            self._grid.pop(value)
        else:
            self._grid[key] = value

        self._call_grid_listeners(key, value)

    def __getitem__(self, item: Pos):
        self._grid.get(item, self._default)

    def __len__(self):
        return len(self._grid)
