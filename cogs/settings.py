"""Server settings cog."""
import os
import gearbox
cog = gearbox.Cog()


@cog.command(permissions='manage_server')
def prefix(server_ex, command: {'get', 'add', 'del', 'reset'}='get', *args):
    """Display or change prefix settings for the current server.

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


@cog.command(permissions='manage_server')
def breaker(server_ex, command: {'get', 'set'}='get', new_breaker=None):
    """Display or change breaker character for the current server."""
    command = command.lower()
    if command == 'get':
        return f"The breaker character for this server is `{server_ex.config['breaker']}`"
    elif command == 'set':
        if new_breaker is None:
            return "Please use `set <breaker_character>`"
        if len(new_breaker) != 1:
            return "The breaker character should be a single character"
        server_ex.config['breaker'] = new_breaker
        return f"The breaker character for this server has been set to `{new_breaker}`"


@cog.command(permissions='manage_server')
def lang(server_ex, language=None):
    """Display or change server language."""
    available_languages = os.listdir(gearbox.CFG['path']['locale'])
    if language is None or language not in available_languages:
        output = f"Current server language: {server_ex.config['language']}\n" if language is None else ''
        output += ('Available languages: ' + gearbox.pretty(available_languages, '`%s`') +
                   '\nPlease note that full support is not guaranteed at all.')
        return output
    else:
        server_ex.config['language'] = language
        server_ex.write()
        return f"Server language has been set to `{language}`!"
