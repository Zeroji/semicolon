"""Base module."""
import os
import discord
import socket
import sys

import gearbox
cog = gearbox.Cog(config='yaml')
_ = cog.gettext
ngettext = cog.ngettext


@cog.command(permissions='manage_guild')
def enable(__cogs, guild_ex, *cogs: 'Name of cogs to enable'):
    """Enable cogs for the current server.

    If called with no cogs, displays enabled cogs. Use `*` to enable all cogs."""
    if not cogs:
        return _('Enabled cogs: {enabled_cogs}').format(enabled_cogs=gearbox.pretty(
            [c for c in __cogs.cogs if guild_ex.is_allowed(c)], '`%s`', final=_('and')))
    if cogs == ('*',):
        cogs = guild_ex.blacklist[::]
        if not cogs:
            return _('No cogs are disabled.')
    not_found = [c for c in cogs if c not in __cogs.cogs]
    if not_found:
        return ngettext("{cogs_not_found} doesn't exist", "{cogs_not_found} don't exist", len(not_found))\
            .format(cogs_not_found=gearbox.pretty(not_found, '`%s`', final=_('and')))
    already = [c for c in cogs if c not in guild_ex.blacklist]
    if already:
        return ngettext("{enabled_cogs} is already enabled", "{enabled_cogs} are already enabled", len(already))\
            .format(enabled_cogs=gearbox.pretty(already, '`%s`', final=_('and')))
    else:
        for c in cogs:
            guild_ex.blacklist.remove(c)
        guild_ex.write()
        return _('Enabled {enabled_cogs}').format(enabled_cogs=gearbox.pretty(cogs, '`%s`', _('and')))


@cog.command(permissions='manage_guild')
def disable(__cogs, guild_ex, *cogs: 'Name of cogs to enable'):
    """Disable cogs for the current server.

    If called with no cogs, displays disabled cogs. Use `*` to disable all cogs."""
    if not cogs:
        if not guild_ex.blacklist:
            return _('No cogs are disabled.')
        return _('Disabled cogs: {disabled_cogs}').format(disabled_cogs=gearbox.pretty(guild_ex.blacklist, '`%s`',
                                                                                       final=_('and')))
    if cogs == ('*',):
        cogs = [c for c in __cogs.cogs if c != __name__.split('.')[-1] and c not in guild_ex.blacklist]
        if not cogs:
            return _('No cogs are enabled.')
    not_found = [c for c in cogs if c not in __cogs.cogs]
    if not_found:
        return ngettext("{cogs_not_found} doesn't exist", "{cogs_not_found} don't exist", len(not_found))\
            .format(cogs_not_found=gearbox.pretty(not_found, '`%s`', final=_('and')))
    if any([c == __name__.split('.')[-1] for c in cogs]):
        return _('Error: cannot disable self')
    already = [c for c in cogs if c in guild_ex.blacklist]
    if already:
        return ngettext("{disabled_cogs} is already disabled", "{disabled_cogs} are already disabled", len(already))\
            .format(disabled_cogs=gearbox.pretty(already, '`%s`', final=_('and')))
    else:
        guild_ex.blacklist.extend(cogs)
        guild_ex.write()
        return _('Disabled {disabled_cogs}').format(disabled_cogs=gearbox.pretty(cogs, '`%s`', final=_('and')))


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
def halp(__cogs, guild_ex, flags, permissions, name: 'Cog or command name'=None):
    """Display information on a cog or command.

    Display general help when called without parameter, or list commands in a cog, or list command information.
    `<argument>` means an argument is mandatory, `[argument]` means you can omit it.
    Display special documentation pages when called with `-d [page]`"""
    if 'd' in flags:
        doc_path = cog.config['help']['doc_path']
        pages = [page[:-3] for page in os.listdir(doc_path) if page.endswith('.md')]
        if name is None or name not in pages:
            return ngettext("The following special documentation page is available:\n{pages}",
                            "The following special documentation pages are available:\n{pages}", len(pages)).format(
                pages=gearbox.pretty(pages, '`%s`', final=_('and')))
        else:
            return markdown_parser(open(f'{doc_path}/{name}.md').read())
    width = cog.config['help']['width']
    active_cogs = [cogg for cogg in __cogs.cogs if guild_ex.is_allowed(cogg)]
    commands = __cogs.command(name, guild_ex, permissions)
    if name is not None and '.' in name:
        cogg, temp_name = name.rsplit('.', 1)
        if cogg in active_cogs and __cogs.cogs[cogg].cog.get(temp_name, permissions):
            commands = [((cogg, temp_name), __cogs.cogs[cogg].cog.get(temp_name, permissions))]
    if name is None:
        return _("Hi, I'm `;;` :no_mouth: I'm split into several cogs, type `;help <cog>` for more information\n") + \
               ngettext("The following cog is currently enabled: {active_cogs}",
                        "The following cogs are currently enabled: {active_cogs}", len(active_cogs)).format(
                   active_cogs=gearbox.pretty(active_cogs, '`%s`', final=_('and')))
    elif name in active_cogs:
        cogg = __cogs.cogs[name]
        output = f'`{name}` - ' + cogg.__doc__.replace('\n\n', '\n')
        for cname, command in cogg.cog.get_all(permissions).items():
            line = cname
            for i, arg in enumerate(command.arguments):
                line += (' <%s>' if i < command.min_arg else ' [%s]') % arg
            output += f'\n`{line:{width}.{width}}|` {command.func.__doc__.splitlines()[0]}'
        if cogg.cog.subcogs:
            output += '\n' + ngettext("The following subcog is available:",
                                      "The following subcogs are available:", len(cogg.cog.subcogs))
            for subname, subcog in cogg.cog.subcogs.items():
                output += f"\n`{subname:{width}.{width}}|` {subcog.__doc__}"
        if commands:
            output += '\n' + ngettext("The following command also exists: {commands}",
                                      "The following commands also exist: {commands}", len(commands)).format(
                commands=gearbox.pretty([f'{cogg}.{__cogs.cogs[cogg].cog.aliases[name]}' for cogg, _ in commands],
                                        '`%s`', final=_('and')))
        return output
    elif commands:
        if len(commands) > 1:
            return _('There are commands in multiple cogs with that name:') + '\n' +\
                   '\n'.join([f'`{cogg + "." + __cogs.cogs[cogg].cog.aliases[name]:{width}.{width}}|` ' +
                              command.func.__doc__.splitlines()[0] for cogg, command in commands])
        if type(commands[0][0]) is not tuple:
            cogg, command = commands[0]
            cname = name
        else:
            (cogg, cname), command = commands[0]
        cname = __cogs.cogs[cogg].cog.aliases[cname]
        complete_name = cogg + '.' + cname
        output = f'`{complete_name}` - **{command.func.__doc__.splitlines()[0]}**'
        aliases = [alias for alias, res in __cogs.cogs[cogg].cog.aliases.items() if res == cname]
        aliases.remove(cname)
        if aliases:
            output += '\n' + _('Also known as: {alias}').format(alias=gearbox.pretty(aliases, '`%s`', final=_('and')))
        output += '\n**' + _('Usage') + '**: `' + complete_name + (' -flags' if command.flags else '')
        for i, arg in enumerate(command.arguments):
            output += (' <%s>' if i < command.min_arg else ' [%s]') % arg
        output += '`'
        if command.flags:
            output += '\n**' + _('Flags') + '**: '
            keys = list(command.flags)
            keys.sort()
            output += gearbox.pretty([f'`-{flag}`' + (f' ({command.flags[flag]})'if command.flags[flag] else '')
                                      for flag in keys])
        if any([arg[0] is not None or len(arg[1]) > 0 for arg in command.annotations.values()]):
            output += '\n**' + _('Arguments') + '**: '
            arguments = []
            for arg in command.arguments:
                anno = command.annotations[arg]
                temp = f'`{arg}`'
                if anno[0] is not None:
                    if type(anno[0]) is set:
                        temp += ' (' + _("must be {list}").format(list=gearbox.pretty(anno[0], "`%s`", _("or"))) + ')'
                    elif type(anno[0]) is not type:
                        temp += ' (' + _("must match `{pattern}`").format(pattern=anno[0].pattern) + ')'
                    else:
                        temp += f' ({anno[0].__name__})'
                if len(anno[1]) > 0:
                    temp += f' ({anno[1]})'
                arguments.append(temp)
            output += gearbox.pretty(arguments, final=_('and'))
        if '\n' in command.func.__doc__:
            output += '\n' + '\n'.join([line.strip() for line in command.func.__doc__.splitlines()[1:] if line])
        return output
    return _('Unknown cog or command.')


@cog.command
@cog.alias('about')
def info():
    """Display basic version information about me."""
    ver = gearbox.prettify_version()
    pver = sys.version.split()[0]
    return _("Hi, I'm `{name}`, a Discord bot written by {author} | {ver} | Python {pver} | discord.py {dver}"
             " | running on {hostname}\nMy source code is available on GitHub: <{link}>").format(
        name=';;', author='Zeroji', link='https://github.com/Zeroji/semicolon/releases/latest',
        ver=ver, pver=pver, dver=discord.__version__, hostname=socket.gethostname()
    )
