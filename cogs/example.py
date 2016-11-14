"""Example cog."""
import asyncio
import gearbox
cog = gearbox.Cog('example')


@cog.command
@cog.alias('hi')
def hello(author):
    """Say hello."""
    return f'Hello, {author.name}!'


@cog.command(fulltext=True)
def say(text):
    """Say that again?"""
    return text


@cog.command(fulltext=True, delete_message=True)
def sayd(text):
    """Scratch that."""
    return text


@cog.command
def join(separator, *args):
    """Join us!"""
    return separator.join(args)


async def call_later(delay, func, *args):
    """Delay a coroutine call"""
    await asyncio.sleep(delay)
    await func(*args)


@cog.command(fulltext=True)
async def timer(client, channel, author, delay, text):
    """Send a message to your future self."""
    await call_later(float(delay), client.send_message, channel, f'{author.mention} {text}')


@cog.command(flags='abc')
def flag(flags):
    return f'I got the following flags: {flags}'
