"""Server settings cog."""
import os
import gearbox
import arrow
cog = gearbox.Cog()
_ = cog.gettext
ngettext = cog.ngettext


DEFAULT_PREFIX = ';'


@cog.command
@cog.hide
def prefix_fallback(guild_ex):
    """Display prefix settings for the current server."""
    return prefix(guild_ex, command='get')


@cog.command(permissions='manage_guild', fallback='prefix_fallback')
def prefix(guild_ex, command: {'get', 'set', 'add', 'del', 'reset'}='get', *args):
    """Display or change prefix settings for the current server.

    `get`: show prefixes, `set . ? !`: remove prefixes and set new ones, `add . ? !`: add prefixes, `del . ? !`: remove prefixes, `reset`: reset back to `;`"""
    command = command.lower()
    if command == 'get':
        if len(guild_ex.prefixes) == 0:
            return _('This server has no prefix. Use `prefix add` to add some!')
        return ngettext("The prefix for this server is {prefixes}",
                        "The prefixes for this server are {prefixes}", len(guild_ex.prefixes)).format(
            prefixes=gearbox.pretty(guild_ex.prefixes, '`%s`', final=_('and')))
    elif command == 'add' or command == 'set':
        if not args:
            return _('Please specify which prefix(es) should be added.')
        if command == 'set':
            for pref in guild_ex.prefixes[::]:
                guild_ex.prefixes.remove(pref)
        overlap = [pref for pref in args if pref in guild_ex.prefixes]
        if overlap:
            return ngettext("{prefixes} is already used", "{prefixes} are already used", len(overlap)).format(
                prefixes=gearbox.pretty(overlap, '`%s`', final=_('and')))
        else:
            n = 0
            for pref in args:  # Not using .extend() in case of duplicates in args
                if pref not in guild_ex.prefixes:
                    guild_ex.prefixes.append(pref)
                    n += 1
            guild_ex.write()
            return ngettext("Added {n} prefix.", "Added {n} prefixes.", n).format(n=n)
    elif command == 'del':
        if not args:
            return _('Please specify which prefix(es) should be deleted.')
        unused = [pref for pref in args if pref not in guild_ex.prefixes]
        if unused:
            return ngettext("{prefixes} isn't used", "{prefixes} aren't used", len(unused)).format(
                prefixes=gearbox.pretty(unused, '`%s`', final=_('and')))
        else:
            n = 0
            for pref in args:
                if pref in guild_ex.prefixes:
                    guild_ex.prefixes.remove(pref)
                    n += 1
            guild_ex.write()
            return ngettext("Removed {n} prefix.", "Removed {n} prefixes.", n).format(n=n)
    elif command == 'reset':
        guild_ex.prefixes = [DEFAULT_PREFIX]
        guild_ex.write()
        return _('Server prefix reset to `{default}`.').format(default=DEFAULT_PREFIX)


@cog.command
@cog.hide
def breaker_fallback(guild_ex):
    """Display breaker settings for the current server."""
    return breaker(guild_ex, command='get')


@cog.command(permissions='manage_guild', fallback='breaker_fallback')
def breaker(guild_ex, command: {'get', 'set'}='get', new_breaker=None):
    """Display or change breaker character for the current server."""
    command = command.lower()
    if command == 'get':
        return _("The breaker character for this server is `{breaker}`").format(breaker=guild_ex.config['breaker'])
    elif command == 'set':
        if new_breaker is None:
            return _("Please use `set <breaker_character>`")
        if len(new_breaker) != 1:
            return _("The breaker character should be a single character")
        guild_ex.config['breaker'] = new_breaker
        return _("The breaker character for this server has been set to `{breaker}`").format(breaker=new_breaker)


@cog.command
@cog.hide
def lang_fallback(guild_ex):
    """Display server language."""
    return lang(guild_ex)


@cog.command(permissions='manage_guild', fallback='lang_fallback')
def lang(guild_ex, language=None):
    """Display or change server language."""
    available_languages = os.listdir(gearbox.CFG['path']['locale'])
    try:  # Hide the 'templates' directory containing .pot files
        available_languages.remove('templates')
    except ValueError:
        pass
    if language is None or language not in available_languages:
        output = ''
        if language is None:
            output = _("Current server language: {language}").format(language=guild_ex.config['language']) + "\n"
        output += (_('Available languages: {languages}').format(languages=gearbox.pretty(available_languages,
                                                                                         '`%s`', final=_('and'))) +
                   '\n' + _('Please note that full support is not guaranteed at all.'))
        return output
    else:
        guild_ex.config['language'] = language
        guild_ex.write()
        output = _("Server language has been set to `{language}`!").format(language=language)
        if '_' in language:
            output += f' :flag_{language.split("_")[-1].lower()}:'
        return output


@cog.command
@cog.hide
def timezone_fallback(guild_ex):
    """Display server timezone."""
    return timezone(guild_ex)


@cog.command(permissions='manage_guild', fallback='timezone_fallback')
def timezone(guild_ex, timezone_code: 'for example Europe/Paris or GMT+1'=None):
    """Display or change server timezone.

    Timezone names should be either in the Zone/City format, for example Europe/Paris or Pacific/Auckland);
    or in the GMT format, for example GMT+1 or GMT-6. Full list at <https://timezonedb.com/time-zones>."""
    utc_now = arrow.utcnow()
    zone = guild_ex.config['timezone']
    if timezone_code is None:
        return _("Current server timezone: {timezone}. The current time is {time}.").format(
            timezone=zone, time=utc_now.to(zone).format(_("HH:mm")))
    try:
        local_now = utc_now.to(timezone_code)
    except arrow.parser.ParserError:
        return _("Invalid timezone name! Please use Zone/City format (see here: <https://timezonedb.com/time-zones>)")
    else:
        guild_ex.config['timezone'] = timezone_code
        guild_ex.write()
        return _("Server timezone has been set to {timezone}. The current time is {time}.").format(
            timezone=timezone_code, time=local_now.format(_('HH:mm')))
