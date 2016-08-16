#!/usr/bin/env python
"""Bot core."""
import argparse
import asyncio
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
        if master not in admins:
            admins = (master,) + admins
        self.master = master
        self.admins = admins
        self.banned = banned
        self.cogs = {}
        self.last_update = time.time()

    def run(self, *args, **kwargs):
        """Start client."""
        super(Bot, self).run(*args, **kwargs)

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
        breaker = '|'  # See README.md
        text = message.content
        if not message.channel.is_private:
            text, is_command = gearbox.strip_prefix(text, prefixes)
            if is_command:
                commands = [text]
            else:
                if breaker * 2 in text:
                    text = text[text.find(breaker * 2) + 2:].lstrip()
                    text, is_command = gearbox.strip_prefix(text, prefixes)
                    if is_command:
                        commands = [text]
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
            commands = [gearbox.strip_prefix(text, prefixes)[0]]

        for text in commands:
            # Very special commands (reload/restart/shutdown)
            if message.author.id in self.admins:
                if text == 'reload':
                    logging.info("Reloading all cogs")
                    for name, cog in cogs.COGS.items():
                        cogs.reload(name, cog)
                if text == 'restart' or (text == 'shutdown' and message.author.id == self.master):
                    logging.info("%s initiated by %s", text.capitalize(), message.author.name)
                    if text == 'shutdown':
                        # An external script runs the bot forever unless this file exists
                        open('stop', 'a').close()
                    for cog in cogs.COGS.values():
                        cog.cog.on_exit()
                    logging.info("All cogs unloaded.")
                    await self.logout()
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
                matches = cogs.command(command)
                if len(matches) > 1:
                    output = ("The command `%s` was found in multiple cogs: %s. Use <cog>.%s to specify." %
                              (command, gearbox.pretty([m[0] for m in matches], '`%s`'), command))
                    await self.send_message(message.channel, output)
                func = matches[0][1] if len(matches) == 1 else None
            if func is not None:
                await func.call(self, message, arguments)

    async def wheel(self):  # They see me loading
        """Dynamically update the cogs."""
        logging.info('Wheel rolling.')
        while True:
            if CFG['wheel']['import']:
                for name in [f[:-3] for f in os.listdir('cogs') if f.endswith('.py')]:
                    if name not in cogs.COGS and gearbox.is_valid(name):
                        cogs.load(name)  # They're addin'
            if CFG['wheel']['reload']:
                for name, cog in cogs.COGS.items():
                    if os.path.getmtime(cog.__file__) > self.last_update:
                        cogs.reload(name, cog)
                        self.last_update = time.time()
            await asyncio.sleep(2)


    async def on_ready(self):
        """Initialization."""
        self.loop.create_task(self.wheel())
        await super(Bot, self).change_status(idle=True)
        logging.info('Client started.')


def main():
    """Load authentication data and run the bot."""
    # Make commandline arguments available
    parser = argparse.ArgumentParser(description='Run semicolon.')
    parser.add_argument('-c', '--config', action='store', metavar='file',
                        help='specify the config file')
    parser.add_argument('-l', '--load', action='append', metavar='cog_name',
                        help='load only specific cogs')
    parser.add_argument('--generate', action='store', metavar='path',
                        help='generate a default configuration file')
    args = parser.parse_args(sys.argv[1:])

    # Generate a default config file
    if args.generate:
        if config.write(args.generate):
            print("Created config file '%s'" % args.generate)
        return

    # Load config and finally start logging
    config.load(args.config, CFG)
    logging.basicConfig(filename=CFG['path']['log'], level=logging.DEBUG,
                        format='%(name)s:%(asctime)s %(levelname)s %(message)s')
    logging.info('Starting...')

    # When in debug mode, load speficic cogs and prevent dynamic import
    if args.load is not None:
        for name in args.load:
            cogs.load(name)
        CFG['wheel']['import'] = False

    token = open(CFG['path']['token'], 'r').read().strip()

    master = open(CFG['path']['master'], 'r').read().strip()
    admins = open(CFG['path']['admins'], 'r').read().splitlines()
    banned = open(CFG['path']['banned'], 'r').read().splitlines()

    bot = Bot(master, tuple(admins), tuple(banned))
    bot.run(token)
    logging.info("Stopped")

if __name__ == '__main__':
    main()
