from __future__ import annotations

import typing as t
import inspect

from flare.converters import get_converter
from flare.exceptions import SerializerError
from flare.utils import gather_iter

if t.TYPE_CHECKING:
    from flare.components import base

__all__: t.Final[t.Sequence[str]] = ("serialize", "deserialize")


async def serialize(cookie: str, types: dict[str, t.Any], kwargs: dict[str, t.Any]) -> str:
    async def serialize_one(k: str, v: t.Any) -> str:
        val = kwargs.get(k)
        converter = get_converter(v)
        tmp = converter.to_str(val)

        if inspect.isawaitable(tmp):
            return await tmp
        else:
            # This is not an awaitable so we can type ignore
            return tmp  # type: ignore

    out = "".join(await gather_iter(serialize_one(k, v) for k, v in types.items()))

    if len(out) > 100:
        raise SerializerError(
            f"The serialized custom_id for component {cookie} may be too long."
            " Try reducing the number of parameters the component takes."
            f" Got length: {len(out)} Expected length: 100 or less"
        )
    return out


async def deserialize(
    custom_id: str, component_map: dict[str, t.Any]
) -> tuple[type[base.SupportsCallback[t.Any]], dict[str, t.Any]]:
    cookie: str | t.Awaitable[str]
    custom_id, cookie = get_converter(str).from_str(custom_id)

    if inspect.isawaitable(cookie):
        cookie = await cookie

    assert isinstance(cookie, str)

    component_ = component_map.get(cookie)

    if component_ is None:
        raise SerializerError(f"Component with cookie {cookie} does not exist.")

    transformed_args: dict[str, t.Any] = {}

    for k, v in component_._dataclass_annotations.items():
        custom_id, value = get_converter(v).from_str(custom_id)
        # TODO: Support for async
        transformed_args[k] = value

    print(transformed_args)

    return (component_, transformed_args)
