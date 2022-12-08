# Modals

Flare supports modals with the `flare.Modal` class.


```python
class ModalTest(flare.Modal, title="My Title"):
    # Values to save
    a: int
    b: str = "1234"

    # Your text inputs.
    text_input: flare.TextInput = flare.TextInput(label="Row 1")
    text_input_2: flare.TextInput = flare.TextInput(label="Row 2")

    async def callback(self, ctx: flare.ModalContext) -> None:
        # You can access text inputs with `self.text_input`.
        # These will be the first two cells in `ctx.values`.
        print(self.text_input.value)
        print(self.text_input_2.value)

        # Access all text input values in an array.
        print(ctx.values)

        await ctx.respond(f"{self.text_input.value, self.text_input_2.value}")
```

Modals can be sent with the `flare.Modal.send` function.

```python
modal = ModalTest(a=5, b="1234")
modal.send(interaction)
```

`flare.TextInput` objects can be added or removed from the modal before it sends. Note that
the `TextInput.value` attribute always reflects the first cells in the array and may not be
accurate if you add or remove `TextInput` objects.

```python
class MyModal(flare.Modal, title="My Title"):
    text_input: flare.TextInput = flare.TextInput(label="default")

    async def callback(self, ctx: flare.ModalContext) -> None:
        ...

modal = MyModal(text_input=flare.TextInput("replaced in __init__"))
modal.append(flare.TextInput(label="new"))
modal[1] = flare.TextInput(label="replaced in array")
```

Modal titles can be set after the instance is created.

```python
class MyModal(flare.Modal):
    async def callback(self, ctx: flare.ModalContext) -> None:
        ...

modal = MyModal().set_title("Set after created!")
modal.send(interaction)
```
