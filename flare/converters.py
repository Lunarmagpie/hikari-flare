import abc
import enum
import functools
import inspect
import struct
import types
import typing as t

import hikari.traits

from flare import exceptions

T = t.TypeVar("T")

__all__: t.Final[t.Sequence[str]] = (
    "Converter",
    "add_converter",
    "StringConverter",
    "IntConverter",
    "EnumConverter",
)


class Converter(abc.ABC, t.Generic[T]):
    """
    Converters are used to convert types between a python object and string.

    .. code-block:: python

        import flare
        import hikari

        class IntConverter(flare.Converter[int]):
            def to_str(self, obj: int) -> str | t.Awaitable[str]:
                return str(obj)

            def from_str(self, obj: str) -> tuple[str, int | t.Awaitable[int]]:
                return int(obj)

        flare.add_converter(int, IntConverter)

        @flare.button(label="Button", style=hikari.ButtonStyle.PRIMARY)
        async def button(
            ctx: flare.MessageContext,
            # `IntConverter` will be used to serialize and deserialize this kwarg.
            number: int,
        ):
            ...


    Attributes:
        type:
            The type that is currently being serialized/deserialized. This will be
            different than the generic type if a subclass of the generic type is being
            serialized/deserialized.
    """

    app: t.ClassVar[hikari.traits.EventManagerAware]

    def __init__(self, type: T) -> None:
        super().__init__()
        self.type = type

    @abc.abstractmethod
    def to_str(self, obj: T) -> str | t.Awaitable[str]:
        """
        Convert an object to a string. Return an awaitable if this needs to be done
        asyncronously.
        """

    @abc.abstractmethod
    def from_str(self, obj: str) -> tuple[str, T | t.Awaitable[T]]:
        """
        Convert a string to this object.

        Returns:
            tuple[str, T | t.Awaitable[T]]:
                The first argument of the function is the remaining characters of the
                string after this element was parsed.
                The second element of the tuple is the parsed object. This object can be
                awaitable if something asyncrounous needs to be done to the data.
        """


_converters: dict[t.Any, tuple[type[Converter[t.Any]], bool]] = {}


def add_converter(t: t.Any, converter: type[Converter[t.Any]], *, supports_subclass: bool = False) -> None:
    """
    Set a converter to be used for a certain type hint and the subclasses of the
    type hint.

    Args:
        t:
            The type this converter supports.
        converter: The converter object.
        supports_subclass:
            If `True`, this converter will be used for subclasses of `t`.
    """
    _converters[t] = (converter, supports_subclass)
    get_converter.cache_clear()


def _any_issubclass(t: t.Any, cls: t.Any) -> bool:
    if not inspect.isclass(t):
        return False
    return issubclass(t, cls)


def _is_union(obj: t.Any) -> bool:
    origin: t.Any = t.get_origin(obj)
    return origin is types.UnionType or origin is t.Union


def _get_left(obj: t.Any) -> t.Any:
    if not _is_union(obj):
        return obj
    return t.get_args(obj)[0]


@functools.lru_cache(maxsize=128)
def get_converter(type_: t.Any) -> Converter[t.Any]:
    """
    Return the converter used for a certain type hint. If a Union is passed,
    the left side of the Union will be used to find the converter.
    """
    origin = _get_left(type_)

    origin_: t.Any = t.get_origin(origin)
    if origin_:
        origin = origin_

    if origin in _converters:
        converter, _ = _converters[origin]
        return converter(origin)
    else:
        for k, (converter, supports_subclass) in _converters.items():
            if supports_subclass and _any_issubclass(origin, k):
                return converter(origin)

    raise exceptions.ConverterError(f"Could not find converter for type `{getattr(type_, '__name__', type_)}`.")


class IntConverter(Converter[int]):
    def to_str(self, obj: int) -> str | t.Awaitable[str]:
        byte_length = obj.bit_length() // 8 + 1
        return get_converter(str).to_str(obj.to_bytes(byte_length, "little").decode("latin1"))

    def from_str(self, obj: str) -> tuple[str, int]:
        remaining, obj = get_converter(str).from_str(obj)  # type: ignore
        return remaining, self.type.from_bytes(obj.encode("latin1"), "little")


class FloatConverter(Converter[float]):
    def to_str(self, obj: float) -> str:
        return struct.pack("d", obj).decode("latin1")

    def from_str(self, obj: str) -> tuple[str, float]:
        obj, remaining = obj[:2], obj[2:]
        return remaining, struct.unpack("d", obj.encode("latin1"))[0]


class StringConverter(Converter[str]):
    def to_str(self, obj: str) -> str:
        length = len(obj)
        byte_length = length.to_bytes(4, "little").decode("latin1")
        return byte_length + obj

    def from_str(self, obj: str) -> tuple[str, str]:
        length = int.from_bytes(obj[0].encode("latin1"), "little")
        string, remaining = obj[1 : length + 1], obj[length + 1 :]
        return remaining, string


class EnumConverter(Converter[enum.Enum]):
    def to_str(self, obj: enum.Enum) -> str | t.Awaitable[str]:
        return get_converter(int).to_str(obj.value)

    def from_str(self, obj: str) -> tuple[str, enum.Enum]:
        remaining, enum = get_converter(int).from_str(obj)
        return remaining, self.type(enum)  # type: ignore


class BoolConverter(Converter[bool]):
    def to_str(self, obj: bool) -> str:
        return "t" if obj else "f"

    def from_str(self, obj: str) -> tuple[str, bool]:
        obj, remaining = obj[0], obj[1:]
        return remaining, obj == "t"


add_converter(float, FloatConverter, supports_subclass=True)
add_converter(int, IntConverter, supports_subclass=True)
add_converter(str, StringConverter, supports_subclass=True)
add_converter(t.Literal, StringConverter)
add_converter(enum.Enum, EnumConverter, supports_subclass=True)
add_converter(bool, BoolConverter)

# MIT License
#
# Copyright (c) 2022-present Lunarmagpie
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
