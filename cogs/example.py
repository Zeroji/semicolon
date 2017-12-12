"""Example cog."""
import asyncio
import discord
import gearbox
cog = gearbox.Cog()
_ = cog.gettext


@cog.command
@cog.alias('hi')
def hello(author):
    """Say hello.

    Basic test command to check that the main parts are working."""
    return _('Hello, {name}!').format(name=author.name)


@cog.command(fulltext=True)
def say(text):
    """Repeat a message."""
    return text


@cog.command(fulltext=True, delete_message=True)
def sayd(text):
    """Repeat a message, delete yours."""
    return text


@cog.command
def join(separator, *words):
    """Insert a separator between words."""
    return separator.join(words)


async def call_later(delay, func, *args):
    """Delay a coroutine call"""
    await asyncio.sleep(delay)
    await func(*args)


@cog.command(fulltext=True)
async def timer(client, channel, author, delay: (int, 'in seconds'), text):
    """Send a message to your future self.

    After a specified time, this will mention you with the message you chose."""
    await call_later(float(delay), client.send_message, channel, f'{author.mention} {text}')


@cog.command(flags='abc')
def flag(flags):
    """Flag test function."""
    return _('I got the following flags: {flags}').format(flags=flags)


@cog.command
def color(red: int, green: int, blue: int):
    """Embed color test function."""
    return discord.Embed(title=f'RGB {red}, {green}, {blue}', color=(red*256+green)*256+blue)


@cog.event
def on_ready():
    """Example event handler.

    This will execute when the on_ready event is triggered by Discord."""
    print('Event dispatch is working!')
