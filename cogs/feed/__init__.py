"""Feed notifier cogs."""
import gearbox
cog = gearbox.Cog(config='json')
_ = cog.gettext


KEY_MAIN_CHAN = 'feed.main_channel'


@cog.command(permissions='manage_channels')
def setchannel(server_ex, server, channel_name=None):
    if channel_name is None:
        channel_id = server_ex.config.get(KEY_MAIN_CHAN)
        if channel_id is None:
            return _('No notification channel specified for this server, {general} will be used').format(
                general=server.default_channel.mention)
        else:
            return _('The main notification channel for this server is {channel}').format(channel='<#%s>' % channel_id)
    channel = gearbox.str_to_chan(server, channel_name)
    if not channel:
        return _('Unknown channel, try using #channel')
    server_ex.config[KEY_MAIN_CHAN] = channel.id
    server_ex.write()
    return _('The main notification channel for this server has been set to {channel}').format(channel=channel.mention)


@cog.command(permissions='manage_channels')
def unsetchannel(server_ex, server):
    if KEY_MAIN_CHAN in server_ex.config:
        server_ex.config.pop(KEY_MAIN_CHAN)
        server_ex.write()
    return _('Reset main notification channel for this server. {general} will be used.').format(
        general=server.default_channel.mention)
