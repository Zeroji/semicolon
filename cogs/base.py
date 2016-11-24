"""Base module."""
import gearbox
cog = gearbox.Cog(__name__.split('.')[-1])


@cog.command(permissions='manage_server')
def enable(server_ex, cog_name):
    """Enable cog for server."""
    if cog_name not in server_ex.blacklist:
        return 'Cog already enabled'
    else:
        server_ex.blacklist.remove(cog_name)
        server_ex.write()
        return f'Enabled {cog_name}'


@cog.command(permissions='manage_server')
def disable(server_ex, cog_name):
    """Disable cog for server."""
    if cog_name == __name__.split('.')[-1]:
        return 'Error: cannot disable self'
    if cog_name in server_ex.blacklist:
        return 'Cog already disabled'
    else:
        server_ex.blacklist.append(cog_name)
        server_ex.write()
        return f'Disabled {cog_name}'


HELP_WIDTH = 29


@cog.command
@cog.alias('halp')
@cog.rename('help')
def halp(__cogs, server_ex, name: 'Cog or command name'=None):
    active_cogs = [cog for cog in __cogs.COGS if cog not in server_ex.blacklist]
    commands = __cogs.command(name, server_ex.blacklist)
    if '.' in name:
        cog, cname = name.split('.', 2)
        if cog in active_cogs and __cogs.COGS[cog].cog.get(cname):
            commands = [(cog, __cogs.COGS[cog].cog.get(cname))]
    if name is None:
        return "Hi, I'm `;;` :no_mouth: I'm split into several cogs, type `;help <cog>` for more information\n" \
               f"The following cog{'s are' if len(active_cogs)>1 else ' is'} currently enabled: " \
               f"{gearbox.pretty(active_cogs, '`%s`')}"
    elif name in active_cogs:
        cog = __cogs.COGS[name]
        output = f'`{name}` - ' + cog.__doc__.replace('\n\n', '\n')
        for cname, command in cog.cog.commands.items():
            line = cname;
            for i, arg in enumerate(command.normal):
                line += (' <%s>' if i < command.min_arg else ' [%s]') % arg
            output += f'\n`{line:{HELP_WIDTH}.{HELP_WIDTH}}|` {command.func.__doc__.splitlines()[0]}'
        if commands:
            output += f"\nThe following command{'s' if len(commands) > 1 else ''} " \
                      f"also exist{'s' if len(commands) == 1 else ''}: " +\
                      gearbox.pretty([f'{cog}.{command.func.__name__}' for cog, command in commands], '`%s`')
        return output
    elif commands:
        if len(commands) > 1:
            return 'There are commands in multiple cogs with that name:\n' +\
                   '\n'.join([f'`{cog + "." + command.func.__name__:{HELP_WIDTH}.{HELP_WIDTH}}|` ' +
                              command.func.__doc__.splitlines()[0] for cog, command in commands])
        cog, command = commands[0]
        complete_name = cog + '.' + command.func.__name__
        output = f'`{complete_name}` - {command.func.__doc__.splitlines()[0]}'
        output += '\nUsage: `' + complete_name + (' -flags' if command.flags else '')
        for i, arg in enumerate(command.normal):
            output += (' <%s>' if i < command.min_arg else ' [%s]') % arg
        output += '`'
        if command.flags:
            output += '\nFlags: '
            keys = list(command.flags)
            keys.sort()
            output += gearbox.pretty([f'`-{flag}`' + (f' ({command.flags[flag]})' if command.flags[flag] else '')
                                      for flag in keys])
        if any([arg[0] is not None or len(arg[1]) > 0 for arg in command.annotations.values()]):
            output += '\nArguments: '
            arguments = []
            for arg in command.normal:
                anno = command.annotations[arg]
                temp = f'`{arg}`'
                if anno[0] is not None:
                    if type(anno[0]) is not type:
                        temp += f' (must match `{anno[0].pattern}`'
                    else:
                        temp += f' ({anno[0].__name__})'
                if len(anno[1]) > 0:
                    temp += f' ({anno[1]})'
                arguments.append(temp)
            output += gearbox.pretty(arguments)
        if '\n' in command.func.__doc__:
            output += '\n' + '\n'.join([line.strip() for line in command.func.__doc__.splitlines()[1:] if line])
        return output
    return 'Nah sorry mate dunno about that'
    # return f'I has halp! But no wit {name} :(' + str(dir(__cogs))


@cog.command(permissions='manage_server')
def prefix(server_ex, command='get', *args):
    """Display or modify prefix settings for server."""
    command = command.lower()
    plur = len(server_ex.prefixes)>1
    if command == 'get':
        if len(server_ex.prefixes) == 0:
            return 'This server has no prefix. Use `prefix add` to add some!'
        return f"The prefix{'es' if plur else ''} for this server {'are' if plur else 'is'} " \
               f"{gearbox.pretty(server_ex.prefixes, '`%s`')}"
    elif command == 'add':
        if not args:
            return 'Please specify which prefix(es) should be added.'
        overlap = [pref for pref in args if pref in server_ex.prefixes]
        if overlap:
            return f"{gearbox.pretty(overlap, '`%s`')} {'are' if len(overlap)>1 else 'is'} already used"
        else:
            n = 0
            for pref in args:  # Not using .extend() in case of duplicates in args
                if pref not in server_ex.prefixes:
                    server_ex.prefixes.append(pref)
                    n += 1
            server_ex.write()
            return f"Added {n} prefix{'es' if n>1 else ''}."
    elif command == 'del':
        if not args:
            return 'Please specify which prefix(es) should be deleted.'
        unused = [pref for pref in args if pref not in server_ex.prefixes]
        if unused:
            return f"{gearbox.pretty(unused, '`%s`')} {'are' if len(unused)>1 else 'is'}""n't used"
        else:
            n = 0
            for pref in args:
                if pref in server_ex.prefixes:
                    server_ex.prefixes.remove(pref)
                    n += 1
            server_ex.write()
            return f"Removed {n} prefix{'es' if n>1 else ''}."
    elif command == 'reset':
        server_ex.prefixes = [';']
        server_ex.write()
        return 'Server prefix reset to `;`.'
