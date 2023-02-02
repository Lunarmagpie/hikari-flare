from __future__ import annotations

import abc
import typing as t

import sigparse
import typing_extensions

from flare import dataclass
from flare.components import base

if t.TYPE_CHECKING:
    from flare import context

__all__: t.Sequence[str] = ("FunctionalComponent",)

P = typing_extensions.ParamSpec("P")
T_co = t.TypeVar("T_co", bound="base.CallbackComponent", covariant=True)


class ComponentTypeProto(t.Protocol[P, T_co]):
    def __new__(cls, *args: P.args, **kwargs: P.kwargs) -> T_co:
        ...

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T_co:
        ...


class FunctionalComponent(abc.ABC, t.Generic[T_co]):
    """
    Decorator to wrap a component function callback so it can be treated as a
    class internally. This should be inherited to create decorators for
    specific component types.
    """

    # This function is a python moment.
    # Just trust that it works.
    def __call__(
        self, callback_: t.Callable[typing_extensions.Concatenate[context.MessageContext, P], t.Any]
    ) -> type[ComponentTypeProto[P, T_co]]:
        """
        Create and return proxy class for `callback`.
        """
        params = [
            dataclass.Field(param.name, param.default, param.annotation) for param in sigparse.sigparse(callback_)[1:]
        ]

        # If the user provides a cookie, use that cookie.
        # If a user does not provide a cookie, create one based on the
        # callback's module and name.
        kwargs = self.kwargs
        kwargs["cookie"] = (
            kwargs["cookie"]
            if kwargs.get("cookie") is not None
            else base.write_cookie(f"{callback_.__module__}.{callback_.__name__}")
        )

        # This is a python moment.
        class Inner(self.component_type, _dataclass_fields=params, **kwargs):  # type: ignore
            async def callback(self, ctx: context.MessageContext):
                kwargs = self._dataclass_values  # type: ignore
                await callback_(ctx, **kwargs)  # type: ignore

        Inner.__name__ = callback_.__name__

        return Inner  # type: ignore

    @property
    @abc.abstractmethod
    def component_type(self) -> type[T_co]:
        """The component type."""

    @property
    @abc.abstractmethod
    def kwargs(self) -> dict[str, t.Any]:
        """The kwargs for `__init_subclass__`"""


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
