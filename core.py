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
log = logging.getLogger('semi.core')


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
        # id:gearbox.Guild mapping of guilds (PMs use the channel ID)
        self.guilds_ex = {}

    def get_guild_ex(self, message_or_id):
        """Return an extended guild object from its ID or a message."""
        # Getting guild information
        # The `gearbox.Guild` class contains additional information about a guild, and is used
        # to preserve guild-specific settings. `guild_ex` stands for "guild extended" and can
        # be used as a special argument in a command.
        # `self.guilds_ex` contains a guild_id:guild_ex mapping to easily access guild settings
        if isinstance(message_or_id, discord.Message):
            if isinstance(message_or_id.channel, discord.abc.GuildChannel):
                guild_ex_id = message_or_id.guild.id
            else:
                guild_ex_id = message_or_id.channel.id
        else:
            guild_ex_id = message_or_id
        if guild_ex_id not in self.guilds_ex:
            self.guilds_ex[guild_ex_id] = gearbox.Guild(guild_ex_id, CFG['path']['guild'])
        return self.guilds_ex[guild_ex_id]

    def run(self, *args, **kwargs):
        """Start client."""
        # Load the cogs while starting the bot
        self.exit_status = 0
        self.loop.create_task(self.wheel())
        super(Bot, self).run(*args, **kwargs)
        return self.exit_status

    async def on_message(self, message):
        """Handle messages."""
        # Avoid replying to self [TEMP]
        if message.author == self.user:
            return

        # Forbid banned users from issuing commands
        if message.author.id in self.banned:
            return

        guild_ex = self.get_guild_ex(message)

        # Loading prefixes and breaker settings
        prefixes = [self.user.mention, self.user.mention.replace('<@', '<@!')]
        prefixes.extend(guild_ex.prefixes)
        breaker = guild_ex.config['breaker']

        # Extracting commands
        commands, command_only = gearbox.read_commands(message.content, prefixes, breaker,
                                                       isinstance(message.channel, discord.abc.PrivateChannel))

        for command in commands:
            await self.process(command, command_only, message, guild_ex)

    async def process(self, command, command_only, message, guild_ex):
        # Very special commands (reload/restart/shutdown)
        if command in ('reload', 'restart', 'shutdown'):
            if message.author.id not in self.admins:
                return
            if command == 'reload':
                log.info("Reloading all cogs")
                for name, cog in cogs.cogs:
                    cogs.reload(name, cog)
            # Admins can restart the bot if it goes wild, but only owner may stop it completely
            if command == 'restart' or (command == 'shutdown' and message.author.id == self.master):
                log.info("%s initiated by %s", command.capitalize(), message.author.name)
                if command == 'shutdown':
                    self.exit_status = 69  # Exit
                else:
                    self.exit_status = 82  # Restart
                for cog in cogs:
                    cog.on_exit()
                log.info("All cogs unloaded.")
                self.ws_server.close()
                await self.change_presence(activity=None)
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
            if not guild_ex.is_allowed(cog_name):
                return
            cog = cogs.cog(cog_name)
            if not cog:
                return
            func = cog.get(cmd, permissions)
        else:
            # Checking for command existence / possible duplicates
            matches = cogs.command(command, guild_ex, permissions)
            if len(matches) > 1:
                await message.channel.send(gearbox.duplicate_command_message(
                    command, matches, guild_ex.config['language']))
            func = matches[0][1] if len(matches) == 1 else None
        if func is not None:
            await func.call(self, message, arguments, cogs)
            if (func.delete_message and command_only and
                    message.channel.permissions_for(
                        message.guild.get_member(self.user.id)).manage_messages):
                await message.delete()

    async def on_socket(self, socket, path):
        async for data in socket:
            for cog in cogs:
                await cog.on_socket_data(self, data, socket, path)

    def dispatch(self, event, *args, **kwargs):
        """Override base event dispatch to call cogs event handlers."""
        super().dispatch(event, *args, **kwargs)
        inferred = None
        guild_ex = None
        method = 'on_' + event
        for cog in cogs:
            if method in cog.events:
                if inferred is None:
                    inferred = gearbox.infer_arguments(args, self, None)
                    guild_ex = inferred.get('guild_ex')
                if guild_ex is None or guild_ex.is_allowed(cog.name):
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
                            log.critical("Sub-cog %s from cog %s couldn't be loaded because "
                                         "a command with the same name exists", name, parent_cog.name)
                            continue
                        name = base_name + name
                        if name not in cogs.cogs and name not in cogs.fail:
                            cogs.load(name)
                            if parent_cog is not None:
                                parent_cog.subcogs[name] = cogs.cogs[name]
                                cogs.cogs[name].cog.parent = parent_cog
                # If a directory containing `__init__.py` is found, load the init and the directory
                elif os.path.isdir(full) and gearbox.is_valid(name) and not (name in cogs.cogs or name in cogs.fail):
                    if parent_cog is not None and name in parent_cog.aliases:
                        log.critical("Sub-cog %s from cog %s couldn't be loaded because "
                                     "a command with the same name exists", name, parent_cog.name)
                        continue
                    if '__init__.py' in os.listdir(full):
                        cogs.load(name)
                        if parent_cog is not None:
                            parent_cog.subcogs[name] = cogs.cogs[name]
                        load_dir(full, base_name + name + '.', cogs.cogs[name].cog)

        log.info('Wheel rolling.')
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
                    cogs.cogs.pop(name, None)

            await asyncio.sleep(2)

    async def on_ready(self):
        """Initialization."""
        self.ws_server = await websockets.serve(self.on_socket, 'localhost', CFG['port']['websocket'])
        version = gearbox.prettify_version(abbrev=0)
        game = discord.Game(version)
        await super(Bot, self).change_presence(status=discord.Status.idle, activity=game)
        log.info('Client started.')


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
    log.info('Starting...')

    # When in debug mode, load specific cogs and prevent dynamic import
    if args.load is not None:
        for name in args.load:
            cogs.load(name)
        CFG['wheel']['import'] = False

    token = open(CFG['path']['token'], 'r').read().strip()

    master = int(open(CFG['path']['master'], 'r').read().strip())
    admins = list(map(int, open(CFG['path']['admins'], 'r').read().splitlines()))
    banned = list(map(int, open(CFG['path']['banned'], 'r').read().splitlines()))

    bot = Bot(master, admins, banned)
    status = bot.run(token)
    log.info("Stopped")
    exit(status)

if __name__ == '__main__':
    main()
