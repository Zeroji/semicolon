#!/usr/bin/env python
"""Bot core."""
import argparse
import asyncio
import importlib
import logging
import os.path
import sys
import time
import discord
import cogs
import config
import gearbox


CFG = {}


class Bot(discord.Client):
    """Client wrapper."""

    def __init__(self, master='', admins=(), banned=()):
        """Magic method docstring."""
        super(Bot, self).__init__()
        self.master = master
        self.admins = admins
        self.banned = banned
        self.cogs = {}
        self.last_update = time.time()

    def run(self, *args):
        """Start client."""
        super(Bot, self).run(*args)

    async def on_message(self, message):
        """Handle messages."""
        # Avoid non-dev servers [TEMP] (Imgur ARGs & Nightcore Reality)
        if message.channel.is_private or message.server.id in \
                ('133648084671528961', '91460936186990592', '211982476745113601'):
            return
        # Avoid replying to self [TEMP]
        if message.author == self.user:
            return

        # Detecting and stripping prefixes
        prefixes = [';']
        prefixes.append(self.user.mention)
        breaker = '|'
        text = message.content
        if not message.channel.is_private:
            text, is_command = gearbox.strip_prefix(text, prefixes)
            if is_command:
                commands = (text,)
            else:
                if breaker * 2 in text:
                    text = text[text.find(breaker * 2) + 2:].lstrip()
                    text, is_command = gearbox.strip_prefix(text, prefixes)
                    if is_command:
                        commands = (text,)
                elif breaker in text:
                    parts = [part.strip() for part in text.split(breaker)]
                    commands = []
                    for part in parts:
                        part, is_command = gearbox.strip_prefix(part, prefixes)
                        if is_command:
                            commands.append(part)
                    is_command = len(parts) > 0
                if not is_command:
                    return
        else:
            commands = (gearbox.strip_prefix(text, prefixes)[0],)

        for text in commands:
            # Getting command arguments (or not)
            if ' ' in text:
                command, arguments = text.split(' ', 1)
            else:
                command, arguments = text, ''

            if '.' in command:
                # Getting command from cog when using cog.command
                cog, cmd = command.split('.')
                cog = cogs.cog(cog)
                if not cog:
                    return
                func = cog.get(cmd)
            else:
                # Checking for command existence / possible duplicates
                func = cogs.command(command)
                if isinstance(func, list):
                    output = ("The command `%s` was found in multiple cogs: %s. Use <cog>.%s to specify." %
                              (command, gearbox.pretty(func, '`%s`'), command))
                    await self.send_message(message.channel, output)
            if isinstance(func, gearbox.Command):
                await func.call(self, message, arguments)

    async def wheel(self):  # They see me loading
        logging.info('Wheel rolling.')
        while True:
            if CFG['wheel']['import']:
                for name in [f[:-3] for f in os.listdir('cogs') if f.endswith('.py')]:
                    if name not in cogs.COGS and gearbox.is_valid(name):
                        cogs.load(name)  # They're addin'
            if CFG['wheel']['reload']:
                for name, cog in cogs.COGS.items():
                    if os.path.getmtime(cog.__file__) > self.last_update:
                        try:
                            importlib.reload(cog)
                        except Exception as exc:
                            logging.error("Error while reloading '%s': %s", name, exc)
                        else:
                            logging.info("Reloaded '%s'.", name)
                        self.last_update = time.time()
            await asyncio.sleep(2)


    async def on_ready(self):
        """Initialization."""
        self.loop.create_task(self.wheel())
        await super(Bot, self).change_status(idle=True)
        logging.info('Client started.')


def main():
    """Load authentication data and run the bot."""
    parser = argparse.ArgumentParser(description='Run semicolon.')
    parser.add_argument('-c', '--config', action='store')
    parser.add_argument('-l', '--load', action='append')
    parser.add_argument('--generate', action='store')
    args = parser.parse_args(sys.argv[1:])
    if args.generate:
        if config.write(args.generate):
            print("Created config file '%s'" % args.generate)
        return
    config.load(args.config, CFG)

    logging.basicConfig(filename=CFG['path']['log'], level=logging.DEBUG)
    logging.info('Starting...')

    if args.load is not None:
        for name in args.load:
            cogs.load(name)
        CFG['wheel']['import'] = False

    token = open(CFG['path']['token'], 'r').read().strip()

    master = open(CFG['path']['master'], 'r').read().strip()
    admins = open(CFG['path']['admins'], 'r').read().splitlines()
    banned = open(CFG['path']['banned'], 'r').read().splitlines()

    bot = Bot(master, admins, banned)
    bot.run(token)

if __name__ == '__main__':
    main()
