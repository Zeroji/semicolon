"""Base module."""
import os
import discord
import sys

import gearbox
cog = gearbox.Cog(config='yaml')


@cog.command(permissions='manage_server')
def enable(__cogs, server_ex, *cogs: 'Name of cogs to enable'):
    """Enable cogs for the current server.

    If called with no cogs, displays enabled cogs. Use `*` to enable all cogs."""
    if not cogs:
        return 'Enabled cogs: ' + gearbox.pretty([c for c in __cogs.COGS if server_ex.is_allowed(c)], '`%s`')
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
        doc_path = cog.config['help']['doc_path']
        pages = [page[:-3] for page in os.listdir(doc_path) if page.endswith('.md')]
        if name is None or name not in pages:
            return f"The following special documentation page{'s are' if len(pages) > 1 else ' is'} available:\n" + \
                   gearbox.pretty(pages, '`%s`')
        else:
            return markdown_parser(open(f'{doc_path}/{name}.md').read())
    width = cog.config['help']['width']
    active_cogs = [cogg for cogg in __cogs.COGS if server_ex.is_allowed(cogg)]
    commands = __cogs.command(name, server_ex)
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
            output += f'\n`{line:{width}.{width}}|` {command.func.__doc__.splitlines()[0]}'
        if cogg.cog.subcogs:
            output += f"\nThe following subcog{'s are' if len(cogg.cog.subcogs) > 1 else ' is'} available:"
            for subname, subcog in cogg.cog.subcogs.items():
                output += f"\n`{subname:{width}.{width}}|` {subcog.__doc__}"
        if commands:
            output += f"\nThe following command{'s' if len(commands) > 1 else ''} " \
                      f"also exist{'s' if len(commands) == 1 else ''}: " +\
                      gearbox.pretty([f'{cogg}.{__cogs.COGS[cogg].cog.aliases[name]}' for cogg, _ in commands], '`%s`')
        return output
    elif commands:
        if len(commands) > 1:
            return 'There are commands in multiple cogs with that name:\n' +\
                   '\n'.join([f'`{cogg + "." + __cogs.COGS[cogg].cog.aliases[name]:{width}.{width}}|` ' +
                              command.func.__doc__.splitlines()[0] for cogg, command in commands])
        if type(commands[0][0]) is not tuple:
            cogg, command = commands[0]
            cname = name
        else:
            (cogg, cname), command = commands[0]
        cname = __cogs.COGS[cogg].cog.aliases[cname]
        complete_name = cogg + '.' + cname
        output = f'`{complete_name}` - **{command.func.__doc__.splitlines()[0]}**'
        aliases = [alias for alias, res in __cogs.COGS[cogg].cog.aliases.items() if res == cname]
        aliases.remove(cname)
        if aliases:
            output += '\nAlso known as: ' + gearbox.pretty(aliases, '`%s`')
        output += '\n**Usage**: `' + complete_name + (' -flags' if command.flags else '')
        for i, arg in enumerate(command.normal):
            output += (' <%s>' if i < command.min_arg else ' [%s]') % arg
        output += '`'
        if command.flags:
            output += '\n**Flags**: '
            keys = list(command.flags)
            keys.sort()
            output += gearbox.pretty([f'`-{flag}`' + (f' ({command.flags[flag]})'if command.flags[flag] else '')
                                      for flag in keys])
        if any([arg[0] is not None or len(arg[1]) > 0 for arg in command.annotations.values()]):
            output += '\n**Arguments**: '
            arguments = []
            for arg in command.normal:
                anno = command.annotations[arg]
                temp = f'`{arg}`'
                if anno[0] is not None:
                    if type(anno[0]) is set:
                        temp += f' (must be {gearbox.pretty(anno[0], "`%s`", "or")})'
                    elif type(anno[0]) is not type:
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


@cog.command
@cog.alias('about')
def info():
    """Display basic version information about me."""
    ver = 'v' + gearbox.version + (' :warning:' if gearbox.version_is_dev else '')
    pver = sys.version.split()[0]
    return f"Hi, I'm `;;`, a Discord bot written by Zeroji | {ver} | Python {pver} | discord.py {discord.__version__}" \
           f"\nMy source code is available on GitHub: <https://github.com/Zeroji/semicolon/releases/latest>"
