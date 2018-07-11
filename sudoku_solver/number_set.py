import copy
import typing


class NumberSet:
    def __init__(self, size: int = 0):
        self._size = size
        self._data = self._mask(size) - 1

    @staticmethod
    def _mask(value: int) -> int:
        return 1 << value

    @classmethod
    def _retrieve_data(cls, numbers) -> int:
        if isinstance(numbers, cls):
            return numbers._data
        elif isinstance(numbers, int):
            return cls._mask(numbers)
        elif isinstance(numbers, typing.Iterable):
            data = 0
            for number in numbers:
                data |= cls._mask(number)
            return data
        else:
            raise TypeError(f'cannot retrieve data from type {type(numbers)}')

    def set(self, numbers: typing.Union['NumberSet', int, typing.Iterable[int]]) -> bool:
        """Returns True if numbers changed."""
        data = self._data
        self._data = self._retrieve_data(numbers)
        return data != self._data

    def retain(self, numbers: typing.Union['NumberSet', int, typing.Iterable[int]]) -> bool:
        """Returns True if numbers changed."""
        data = self._data
        self._data &= self._retrieve_data(numbers)
        return data != self._data

    def add(self, numbers: typing.Union['NumberSet', int, typing.Iterable[int]]) -> bool:
        """Returns True if numbers changed."""
        data = self._data
        self._data |= self._retrieve_data(numbers)
        return data != self._data

    def remove(self, numbers: typing.Union['NumberSet', int, typing.Iterable[int]]) -> bool:
        """Returns True if numbers changed."""
        data = self._data
        self._data &= ~self._retrieve_data(numbers)
        return data != self._data

    def peek(self) -> int:
        """Returns an available number."""
        value = self._data.bit_length() - 1
        return value if value >= 0 else None

    def __len__(self):
        return bin(self._data).count('1')

    def __contains__(self, value: int):
        return bool(self._data & self._mask(value))

    def __iter__(self):
        data = self._data
        value = 0
        while data > 0:
            if (data & 1) == 1:
                yield value

            data >>= 1
            value += 1

    def __iand__(self, other):
        self.retain(other)
        return self

    def __and__(self, other):
        new = copy.copy(self)
        new &= other
        return new

    def __ior__(self, other):
        self.add(other)
        return self

    def __or__(self, other):
        new = copy.copy(self)
        new |= other
        return new

    def __isub__(self, other):
        self.remove(other)
        return self

    def __sub__(self, other):
        new = copy.copy(self)
        new -= other
        return new

    def __repr__(self):
        return ', '.join(str(n) for n in self)
