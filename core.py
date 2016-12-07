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
        self.server = {}

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

        # Getting server information
        server_ex_id = message.channel.id if message.channel.is_private else message.server.id
        if server_ex_id not in self.server:
            self.server[server_ex_id] = gearbox.Server(server_ex_id, CFG['path']['server'])
        server_ex = self.server[server_ex_id]

        # Loading prefixes and breaker settings
        prefixes = [self.user.mention]
        prefixes.extend(server_ex.prefixes)
        breaker = server_ex.config['breaker']

        # Extracting commands
        commands, command_only = gearbox.read_commands(message.content, prefixes, breaker, message.channel.is_private)

        for command in commands:
            await self.process(command, command_only, message, server_ex)

    async def process(self, command, command_only, message, server_ex):
        # Very special commands (reload/restart/shutdown)
        if command in ('reload', 'restart', 'shutdown'):
            if message.author.id not in self.admins:
                return
            if command == 'reload':
                logging.info("Reloading all cogs")
                for name, cog in cogs.COGS.items():
                    cogs.reload(name, cog)
            # Admins can restart the bot if it goes wild, but only owner may stop it completely
            if command == 'restart' or (command == 'shutdown' and message.author.id == self.master):
                logging.info("%s initiated by %s", command.capitalize(), message.author.name)
                if command == 'shutdown':
                    # An external script runs the bot forever unless this file exists
                    open('stop', 'a').close()
                for cog in cogs.COGS.values():
                    cog.cog.on_exit()
                logging.info("All cogs unloaded.")
                await self.change_presence(game=None)
                await self.logout()
            return
        # Getting command arguments (or not)
        if ' ' in command:
            command, arguments = command.split(' ', 1)
        else:
            arguments = ''

        if '.' in command:
            # Getting command from cog when using cog.command
            cog, cmd = command.rsplit('.', 1)
            if not server_ex.is_allowed(cog):
                return
            cog = cogs.cog(cog)
            if not cog:
                return
            func = cog.get(cmd)
        else:
            # Checking for command existence / possible duplicates
            matches = cogs.command(command, server_ex)
            if len(matches) > 1:
                output = f"The command `{command}` was found in multiple cogs: " \
                         f"{gearbox.pretty([m[0] for m in matches], '`%s`')}. Use <cog>.{command} to specify."
                await self.send_message(message.channel, output)
            func = matches[0][1] if len(matches) == 1 else None
        if func is not None and all([permission in message.channel.permissions_for(message.author)
                                     for permission in func.permissions]):
            await func.call(self, message, arguments, cogs)
            if (func.delete_message and command_only and
                    message.channel.permissions_for(
                        message.server.get_member(self.user.id)).manage_messages):
                await self.delete_message(message)

    async def on_reaction_add(self, reaction, user):
        await self.on_reaction(True, reaction, user)

    async def on_reaction_remove(self, reaction, user):
        await self.on_reaction(False, reaction, user)

    async def on_reaction(self, added, reaction, user):
        for cog in cogs.COGS:
            await cogs.COGS.get(cog).cog.on_reaction_any(self, added, reaction, user)

    async def wheel(self):  # They see me loading
        """Dynamically update the cogs."""

        def load_dir(path='cogs', base_name='', parent_cog=None):
            for name in os.listdir(path):
                full = os.path.join(path, name)
                if name.endswith('.py'):
                    name = name[:-3]
                    if gearbox.is_valid(name):
                        if parent_cog is not None and name in parent_cog.aliases:
                            logging.critical("Sub-cog %s from cog %s couldn't be loaded because "
                                             "a command with the same name exists", name, parent_cog.name)
                            continue
                        name = base_name + name
                        if name not in cogs.COGS:
                            cogs.load(name)
                            if parent_cog is not None:
                                parent_cog.subcogs[name] = cogs.COGS[name]
                elif os.path.isdir(full) and gearbox.is_valid(name) and name not in cogs.COGS :
                    if parent_cog is not None and name in parent_cog.aliases:
                        logging.critical("Sub-cog %s from cog %s couldn't be loaded because "
                                         "a command with the same name exists", name, parent_cog.name)
                        continue
                    if '__init__.py' in os.listdir(full):
                        cogs.load(name)
                        if parent_cog is not None:
                            parent_cog.subcogs[name] = cogs.COGS[name]
                        load_dir(full, base_name + name + '.', cogs.COGS[name].cog)

        logging.info('Wheel rolling.')
        while True:
            if CFG['wheel']['import']:
                load_dir()
            if CFG['wheel']['reload']:
                for name, cog in cogs.COGS.items():
                    if os.path.getmtime(cog.__file__) > self.last_update:
                        cogs.reload(name, cog)
                        self.last_update = time.time()
            await asyncio.sleep(2)

    async def on_ready(self):
        """Initialization."""
        self.loop.create_task(self.wheel())
        version = discord.Game()
        version.name = 'v' + gearbox.version
        if gearbox.version_is_dev:
            version.name += ' [dev]'
        await super(Bot, self).change_presence(status=discord.Status.idle, game=version)
        logging.info('Client started.')


def main():
    """Load authentication data and run the bot."""
    # Make commandline arguments available
    parser = argparse.ArgumentParser(description='Run semicolon.')
    parser.add_argument('-c', '--config', action='store', metavar='file',
                        help='specify the config file')
    parser.add_argument('-l', '--load', action='append', metavar='cog_name',
                        help='load only specific cogs')
    args = parser.parse_args(sys.argv[1:])

    # Load config and finally start logging
    try:
        config.load(args.config, CFG)
    except:
        print('FATAL ERROR: cannot continue without configuration')
        raise
    gearbox.update_config(CFG)
    logging.basicConfig(filename=CFG['path']['log'], level=logging.DEBUG,
                        format='%(asctime)s:%(name)s: %(levelname)s %(message)s')
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('websockets').setLevel(logging.WARNING)
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
