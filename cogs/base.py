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
