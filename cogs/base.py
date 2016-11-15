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
