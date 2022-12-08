# Converters

Converters allow you to serialize and deserialize types. Here in an example of an int converter.

```python
# All converters inherit from `Converter[T]` where `T` is the type that they
# convert to a string and back.
class IntConverter(flare.Converter[int]):
    async def to_str(self, obj: int) -> str:
        return str(obj)

    async def from_str(self, obj: str) -> int:
        return int(obj)

# Add the converter to `flare`. Without this, the type will not be converted
# with the converter.
flare.add_converter(
    int,          # The typehint this converter is used for.
    IntConverter  # The converter class.
)
```

```{warning}
Do not use this impl. A more space efficient version of `IntConverter` is enabled by default.
```

Here is an example of converting a more complex custom class.

```{note}
The strings your converters generate should be as short as possible. Only 100 characters can be used
in a component's custom id.
```

```python
import dataclasses
import enum

# An `Enum` with `int` values is used to reduce space when serializing.
class CatBreed(enum.Enum):
    Saimese = enum.auto()
    TabbyCat = enum.auto()

@dataclasses.dataclass
class Cat:
    name: str
    breed: CatBreed

class CatConverter(flare.Converter[Cat]):
    async def to_str(self, obj: Cat) -> str:
        # Space is minimal! Using a format like this is much more space
        # efficient than json.
        return f"{obj.name}:{obj.breed.value}"

    async def from_str(self, obj: str) -> Cat:
        name, breed = obj.split(":")
        return Cat(
            name=name,
            # The `breed` string must be converted to an `int` so it is a
            # valid value of `CatBreed`.
            breed=CatBreed(int(breed))
        )

flare.add_converter(
    Cat,
    CatConverter
)
```


## Converting Subclasses

By default converters will only effect the exact type they convert. They can
also be set to convert subclasses of that type. `self.type` can be accessed to
get the type that is currently being converted.

```python
class SubclassIntConverter(flare.Converter[int]):
    async def to_string(self, obj: int) -> str:
        return str(obj) 

    async def from_str(self, obj: str) -> int:
        # `self.type` is the type that is currently being converted.
        # Examples:
        # - If an int was being converted, `self.type` would be `int`.
        # - If a `hikari.Snowflake` is being converted, `self.type` would
        #   be `hikari.Snowflake`.
        return self.type(obj)


# Add the converter for type `int` and all subtypes of `int`.
flare.add_converter(
    int,
    SubclassIntConverter,
    supports_subclass=True,
)
```
