# Getting Started

## Installation

flare can be installed using pip via the following command:

``$ python3 -m pip install -U hikari-flare``

## What is falre?
`flare` is a component handler that uses the `custom_id` field for components,
which is a unique identifier for a component, to save information. This allows
components to save information between restarts without using a database.

## First steps

How about the typical example from webdev with a counter button?

```python
import hikari
import flare

bot = hikari.GatewayBot("TOKEN")

# This function must be called on startup. `bot` must be an object that
# implements `hikari.traits.EventManagerAware`.
flare.install(bot)


@flare.button(label="Click me!")
async def counter_button(
    ctx: flare.MessageContext,
    # The argument `n` is saved as the state. This argument defaults to 0 if no
    # value is specified in `counter_button()`.
    n: int = 0,
) -> None:
    n += 1
    await ctx.edit_response(
        # The components are edited to update the state.
        component=await flare.Row(counter_button(n=n).set_label(f"Clicked {n} Times!"))
    )


@bot.listen()
async def on_message(event: hikari.MessageCreateEvent):
    if event.message.author.is_bot or not event.message.content:
        return

    me = bot.get_me()

    # If the bot is mentioned
    if me.id in event.message.user_mentions_ids:
        await event.message.respond(
            # When responding to the interaction, use the default values.
            component=await flare.Row(counter_button())
        )

bot.run()
```
