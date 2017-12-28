#!/usr/bin/env python
"""Bot core."""
import argparse
import asyncio
import logging
import os.path
import sys
import time
import discord
import websockets
import config
import gearbox
from cogs import Wrapper
cogs = Wrapper()


# Global variable for configuration
CFG = {}


class Bot(discord.Client):
    """Wrapper for the discord.Client class."""

    def __init__(self, master='', admins=None, banned=None):
        super(Bot, self).__init__()
        if admins is None:
            admins = []
        if master not in admins:
            admins.append(master)
        self.master = master
        self.admins = admins
        self.banned = banned if banned is not None else []
        # name:gearbox.Cog mapping of cogs
        self.cogs = {}
        # last time the cogs file were checked for modifications
        self.last_update = time.time()
        # id:gearbox.Server mapping of servers (PMs use the channel ID)
        self.servers_ex = {}

    def get_server_ex(self, message_or_id):
        """Return an extended server object from its ID or a message."""
        # Getting server information
        # The `gearbox.Server` class contains additional information about a server, and is used
        # to preserve server-specific settings. `server_ex` stands for "server extended" and can
        # be used as a special argument in a command.
        # `self.servers_ex` contains a server_id:server_ex mapping to easily access server settings
        if isinstance(message_or_id, discord.Message):
            if isinstance(message_or_id.channel, discord.abc.GuildChannel):
                server_ex_id = message_or_id.guild.id
            else:
                server_ex_id = message_or_id.channel.id
        else:
            server_ex_id = message_or_id
        if server_ex_id not in self.servers_ex:
            self.servers_ex[server_ex_id] = gearbox.Server(server_ex_id, CFG['path']['server'])
        return self.servers_ex[server_ex_id]

    def run(self, *args, **kwargs):
        """Start client."""
        # Load the cogs while starting the bot
        self.loop.create_task(self.wheel())
        super(Bot, self).run(*args, **kwargs)

    async def on_message(self, message):
        """Handle messages."""
        # Avoid replying to self [TEMP]
        if message.author == self.user:
            return

        # Forbid banned users from issuing commands
        if message.author.id in self.banned:
            return

        server_ex = self.get_server_ex(message)

        # Loading prefixes and breaker settings
        prefixes = [self.user.mention]
        prefixes.extend(server_ex.prefixes)
        breaker = server_ex.config['breaker']

        # Extracting commands
        commands, command_only = gearbox.read_commands(message.content, prefixes, breaker,
                                                       isinstance(message.channel, discord.abc.PrivateChannel))

        for command in commands:
            await self.process(command, command_only, message, server_ex)

    async def process(self, command, command_only, message, server_ex):
        # Very special commands (reload/restart/shutdown)
        if command in ('reload', 'restart', 'shutdown'):
            if message.author.id not in self.admins:
                return
            if command == 'reload':
                logging.info("Reloading all cogs")
                for name, cog in cogs.cogs:
                    cogs.reload(name, cog)
            # Admins can restart the bot if it goes wild, but only owner may stop it completely
            if command == 'restart' or (command == 'shutdown' and message.author.id == self.master):
                logging.info("%s initiated by %s", command.capitalize(), message.author.name)
                if command == 'shutdown':
                    # An external script runs the bot forever unless this file exists
                    open('stop', 'a').close()
                for cog in cogs:
                    cog.on_exit()
                logging.info("All cogs unloaded.")
                await self.change_presence(game=None)
                await self.logout()
            return
        # Getting command arguments (or not)
        if ' ' in command:
            command, arguments = command.split(' ', 1)
        else:
            arguments = ''

        permissions = message.channel.permissions_for(message.author)
        if '.' in command:
            # Getting command from cog when using cog.command
            cog_name, cmd = command.rsplit('.', 1)
            if not server_ex.is_allowed(cog_name):
                return
            cog = cogs.cog(cog_name)
            if not cog:
                return
            func = cog.get(cmd, permissions)
        else:
            # Checking for command existence / possible duplicates
            matches = cogs.command(command, server_ex, permissions)
            if len(matches) > 1:
                await message.channel.send(gearbox.duplicate_command_message(
                    command, matches, server_ex.config['language']))
            func = matches[0][1] if len(matches) == 1 else None
        if func is not None:
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
        """Propagate reaction events to the cogs."""
        for cog in cogs:
            await cog.on_reaction_any(self, added, reaction, user)

    async def on_socket(self, socket, path):
        data = await socket.recv()
        print(type(data), data)
        for cog in cogs:
            await cog.on_socket_data(self, data, socket)

    def dispatch(self, event, *args, **kwargs):
        """Override base event dispatch to call cogs event handlers."""
        super().dispatch(event, *args, **kwargs)
        inferred = gearbox.infer_arguments(args, self, None)
        server_ex = inferred.get('server_ex')
        method = 'on_' + event
        for cog in cogs:
            if server_ex is None or server_ex.is_allowed(cog.name):
                if method in cog.events:
                    self.loop.create_task(cog.events.get(method).call(self, args, inferred))

    async def wheel(self):  # They see me loading
        """Dynamically update the cogs."""

        # Load cogs in a directory
        def load_dir(path='cogs', base_name='', parent_cog=None):
            for name in os.listdir(path):
                full = os.path.join(path, name)
                # If a .py file is found (and valid), try to load it
                if name.endswith('.py'):
                    name = name[:-3]
                    if gearbox.is_valid(name):
                        if parent_cog is not None and name in parent_cog.aliases:
                            logging.critical("Sub-cog %s from cog %s couldn't be loaded because "
                                             "a command with the same name exists", name, parent_cog.name)
                            continue
                        name = base_name + name
                        if name not in cogs.cogs and name not in cogs.fail:
                            cogs.load(name)
                            if parent_cog is not None:
                                parent_cog.subcogs[name] = cogs.cogs[name]
                                cogs.cogs[name].cog.parent = parent_cog
                # If a directory containing `__init__.py` is found, load the init and the directory
                elif os.path.isdir(full) and gearbox.is_valid(name) and name not in cogs.cogs and name not in cogs.fail:
                    if parent_cog is not None and name in parent_cog.aliases:
                        logging.critical("Sub-cog %s from cog %s couldn't be loaded because "
                                         "a command with the same name exists", name, parent_cog.name)
                        continue
                    if '__init__.py' in os.listdir(full):
                        cogs.load(name)
                        if parent_cog is not None:
                            parent_cog.subcogs[name] = cogs.cogs[name]
                        load_dir(full, base_name + name + '.', cogs.cogs[name].cog)

        logging.info('Wheel rolling.')
        while True:
            if CFG['wheel']['import']:
                load_dir()
            if CFG['wheel']['reload']:
                for name, cog in cogs.cogs.items():
                    if os.path.getmtime(cog.__file__) > self.last_update:
                        cogs.reload(name, cog)
                        self.last_update = time.time()
                valid_cogs = set()
                for name in cogs.fail:
                    if os.path.getmtime(os.path.join('cogs', *name.split('.')) + '.py') > self.last_update:
                        cogs.load(name)
                        self.last_update = time.time()
                        if name in cogs.cogs:
                            valid_cogs.add(name)
                for name in valid_cogs:
                    cogs.cogs.remove(name)

            await asyncio.sleep(2)

    async def on_ready(self):
        """Initialization."""
        self.loop.create_task(websockets.serve(self.on_socket, 'localhost', CFG['port']['websocket']))
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

    # When in debug mode, load specific cogs and prevent dynamic import
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
    logging.info("Stopped")

if __name__ == '__main__':
    main()
