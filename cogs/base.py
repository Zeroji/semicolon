"""Base module."""
import os

import gearbox
cog = gearbox.Cog(__name__.split('.')[-1])


@cog.command(permissions='manage_server')
def enable(__cogs, server_ex, *cogs: 'Name of cogs to enable'):
    """Enable cogs for the current server.

    If called with no cogs, displays enabled cogs. Use `*` to enable all cogs."""
    if not cogs:
        return 'Enabled cogs: ' + gearbox.pretty([c for c in __cogs.COGS if c not in server_ex.blacklist], '`%s`')
    print(cogs)
    if cogs == ('*',):
        cogs = server_ex.blacklist[::]
    not_found = [c for c in cogs if c not in __cogs.COGS]
    if not_found:
        return gearbox.pretty(not_found, '`%s`') + f" do{'es' * (len(not_found) == 1)}n't exist"
    already = [c for c in cogs if c not in server_ex.blacklist]
    if already:
        return gearbox.pretty(already, '`%s`') + f" {'are' if len(already) > 1 else 'is'} already enabled"
    else:
        for c in cogs:
            server_ex.blacklist.remove(c)
        server_ex.write()
        return 'Enabled ' + gearbox.pretty(cogs, '`%s`')


@cog.command(permissions='manage_server')
def disable(__cogs, server_ex, *cogs: 'Name of cogs to enable'):
    """Disable cogs for the current server.

    If called with no cogs, displays disabled cogs. Use `*` to disable all cogs."""
    if not cogs:
        if not server_ex.blacklist:
            return 'No cogs are disabled.'
        return 'Disabled cogs: ' + gearbox.pretty(server_ex.blacklist, '`%s`')
    if cogs == ('*',):
        cogs = [c for c in __cogs.COGS if c != __name__.split('.')[-1] and c not in server_ex.blacklist]
    not_found = [c for c in cogs if c not in __cogs.COGS]
    if not_found:
        return gearbox.pretty(not_found, '`%s`') + f" do{'es' * (len(not_found) == 1)}n't exist"
    if any([c == __name__.split('.')[-1] for c in cogs]):
        return 'Error: cannot disable self'
    already = [c for c in cogs if c in server_ex.blacklist]
    if already:
        return gearbox.pretty(already, '`%s`') + f" {'are' if len(already) > 1 else 'is'} already disabled"
    else:
        server_ex.blacklist.extend(cogs)
        server_ex.write()
        return 'Disabled ' + gearbox.pretty(cogs, '`%s`')


HELP_WIDTH = 29  # Size of left part of help messages (command list between backticks)


def markdown_parser(data):
    """Parse regular Markdown to make it more readable by Discord."""
    output = ''
    lines = data.splitlines()
    code_block = False
    for i, line in enumerate(lines):
        if line.startswith('```'):
            code_block = not code_block
            output += line + '\n'
            continue
        if code_block:
            output += line + '\n'
            continue
        if line.endswith('  '):
            output += line[:-2] + '\n'
        elif not line:
            if not output.endswith('\n'):
                output += '\n'
        else:
            output += line + ' '
    return output


@cog.command(flags={'d': 'Show special documentation'})
@cog.alias('halp')
@cog.rename('help')
def halp(__cogs, server_ex, flags, name: 'Cog or command name'=None):
    """Display information on a cog or command.

    Display general help when called without parameter, or list commands in a cog, or list command information.
    `<argument>` means an argument is mandatory, `[argument]` means you can omit it.
    Display special documentation pages when called with `-d [page]`"""
    if 'd' in flags:
        pages = [page[:-3] for page in os.listdir('doc/internal') if page.endswith('.md')]
        if name is None or name not in pages:
            return f"The following special documentation page{'s are' if len(pages) > 1 else ' is'} available:\n" + \
                   gearbox.pretty(pages, '`%s`')
        else:
            return markdown_parser(open('doc/internal/%s.md' % name).read())

    active_cogs = [cogg for cogg in __cogs.COGS if cogg not in server_ex.blacklist]
    commands = __cogs.command(name, server_ex.blacklist)
    if name is not None and '.' in name:
        cogg, temp_name = name.rsplit('.', 1)
        if cogg in active_cogs and __cogs.COGS[cogg].cog.get(temp_name):
            commands = [((cogg, temp_name), __cogs.COGS[cogg].cog.get(temp_name))]
    if name is None:
        return "Hi, I'm `;;` :no_mouth: I'm split into several cogs, type `;help <cog>` for more information\n" \
               f"The following cog{'s are' if len(active_cogs)>1 else ' is'} currently enabled: " \
               f"{gearbox.pretty(active_cogs, '`%s`')}"
    elif name in active_cogs:
        cogg = __cogs.COGS[name]
        output = f'`{name}` - ' + cogg.__doc__.replace('\n\n', '\n')
        for cname, command in cogg.cog.commands.items():
            line = cname
            for i, arg in enumerate(command.normal):
                line += (' <%s>' if i < command.min_arg else ' [%s]') % arg
            output += f'\n`{line:{HELP_WIDTH}.{HELP_WIDTH}}|` {command.func.__doc__.splitlines()[0]}'
        if cogg.cog.subcogs:
            output += f"\nThe following subcog{'s are' if len(cogg.cog.subcogs) > 1 else ' is'} available:"
            for subname, subcog in cogg.cog.subcogs.items():
                output += f"\n`{subname:{HELP_WIDTH}.{HELP_WIDTH}}|` {subcog.__doc__}"
        if commands:
            output += f"\nThe following command{'s' if len(commands) > 1 else ''} " \
                      f"also exist{'s' if len(commands) == 1 else ''}: " +\
                      gearbox.pretty([f'{cogg}.{__cogs.COGS[cogg].cog.aliases[name]}' for cogg, _ in commands], '`%s`')
        return output
    elif commands:
        if len(commands) > 1:
            return 'There are commands in multiple cogs with that name:\n' +\
                   '\n'.join([f'`{cogg + "." + __cogs.COGS[cogg].cog.aliases[name]:{HELP_WIDTH}.{HELP_WIDTH}}|` ' +
                              command.func.__doc__.splitlines()[0] for cogg, command in commands])
        (cogg, cname), command = commands[0]
        cname = __cogs.COGS[cogg].cog.aliases[cname]
        complete_name = cogg + '.' + cname
        output = f'`{complete_name}` - {command.func.__doc__.splitlines()[0]}'
        aliases = [alias for alias, res in __cogs.COGS[cogg].cog.aliases.items() if res == cname]
        aliases.remove(cname)
        if aliases:
            output += '\nAlso known as: ' + gearbox.pretty(aliases, '`%s`')
        output += '\nUsage: `' + complete_name + (' -flags' if command.flags else '')
        for i, arg in enumerate(command.normal):
            output += (' <%s>' if i < command.min_arg else ' [%s]') % arg
        output += '`'
        if command.flags:
            output += '\nFlags: '
            keys = list(command.flags)
            keys.sort()
            output += gearbox.pretty([f'`-{flag}`' + (f' ({command.flags[flag]})'if command.flags[flag] else '')
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
    return 'Unknown cog or command.'


@cog.command(permissions='manage_server')
def prefix(server_ex, command: 'get/add/del/reset'='get', *args):
    """Display or edit prefix settings for the current server.

    `get`: show prefixes, `add . ? !`: add prefixes, `del . ? !`: remove prefixes, `reset`: reset back to `;`"""
    command = command.lower()
    plur = len(server_ex.prefixes) > 1
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
