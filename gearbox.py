"""More like a toolbox, actually."""
import inspect
import logging
import os
import re
import json
import datetime
import discord
import yaml
import config
import gettext
import unittest


class TestGearbox(unittest.TestCase):
    def test_is_valid(self):
        self.assertTrue(is_valid("base"))
        self.assertTrue(is_valid("cog.sub"))
        self.assertTrue(is_valid("under_score"))
        self.assertFalse(is_valid("Base"))
        self.assertFalse(is_valid("cog/sub"))

    def test_pretty(self):
        self.assertEqual(pretty(()), "")
        self.assertEqual(pretty([]), "")
        self.assertEqual(pretty(["a"]), "a")
        self.assertEqual(pretty(["a"], "*%s*"), "*a*")
        self.assertEqual(pretty(["a", "b"], final="and"), "a and b")
        self.assertEqual(pretty(["a", "b", "c"], final="and"), "a, b and c")
        self.assertEqual(pretty(["a", "b", "c"], "*%s*", final="and"), "*a*, *b* and *c*")

    def test_has_prefix(self):
        self.assertTrue(has_prefix(";hi", (';',)))
        self.assertFalse(has_prefix("hi", (';',)))
        self.assertTrue(has_prefix(";hi", (';', '!')))
        self.assertTrue(has_prefix("!hi", (';', '!')))
        self.assertFalse(has_prefix(";hi", ('!',)))

    def test_strip_prefix(self):
        self.assertEqual(strip_prefix(";hi", (';',)), "hi")
        self.assertEqual(strip_prefix("hi", (';',)), "hi")
        self.assertEqual(strip_prefix(";hi", (';', '!')), "hi")
        self.assertEqual(strip_prefix("!hi", (';', '!')), "hi")
        self.assertEqual(strip_prefix(";hi", ('!',)), ";hi")

    def test_read_commands(self):
        self.assertEqual(read_commands(";a b c", [';'], '|', False), (['a b c'], True))
        self.assertEqual(read_commands("|;a b|;c", [';'], '|', False), (['a b', 'c'], False))
        self.assertEqual(read_commands("a b", [';'], '|', True), (['a b'], True))
        self.assertNotEqual(read_commands("a b", [';'], '|', False), (['a b'], True))
        self.assertEqual(read_commands("a b || c", [';'], '|', False), ([], False))
        self.assertEqual(read_commands("a b ||;c", [';'], '|', False), (['c'], False))
        self.assertEqual(read_commands("a |;b || ;c | ;d", [';'], '|', False), (['b', 'c | ;d'], False))


# List of possible special arguments that a command can expect
SPECIAL_ARGS = ('message', 'author', 'channel', 'guild', 'guild_ex', 'client', 'flags', '__cogs', 'permissions')
SPECIAL_TYPES = {discord.Message: 'message', discord.abc.PrivateChannel: 'private_channel',
                 discord.abc.GuildChannel: 'guild_channel', discord.Member: 'member', discord.VoiceState: 'voice_state',
                 discord.User: 'user', discord.Guild: 'guild', discord.Reaction: 'reaction', discord.Emoji: 'emoji',
                 discord.Role: 'role', datetime.datetime: 'when'}  # type: name mapping for argument detection
VALID_NAME = re.compile('[a-z][a-z_.0-9]*$')  # Regular expression all names must match
CONFIG_LOADERS = {'json': json, 'yaml': yaml}  # name:module mapping of config loaders (for cog-specific config files)
CFG = {}  # Configuration settings (nested dictionary)
version = 'unknown'  # version number
version_is_dev = False  # True if dev version, False if release
LANGUAGES = {}  # language_code:translation mapping of all available languages for this module (gearbox)


def update_config(cfg):
    """Update local config from variable.

    Used during startup to load version number file properly and load all locale data, if any."""
    global version, version_is_dev, LANGUAGES
    # Update configuration
    CFG.update(cfg)
    # Try to load version information
    version_path = CFG['path']['version']
    try:
        ver_num, ver_type = open(version_path).read().strip().split()
        version = ver_num  # String matching [0-9]+(?:\.[0-9]+)* for example 0.3.14
        version_is_dev = ver_type == 'dev'  # Expected to be either "dev" or "release"
    except ValueError:
        logging.warning('Wrong version file format! It should be <number> <type>')
    except FileNotFoundError:
        logging.warning('Version file %s not found' % version_path)
    except EnvironmentError as exc:
        logging.warning("Couldn't open version file '%s': %s", version_path, exc)
    # Go through all the directories in the locale folder and load all gearbox.mo translation files
    for lang in os.listdir(CFG['path']['locale']):
        if os.path.isfile(os.path.join(CFG['path']['locale'], lang, 'LC_MESSAGES', 'gearbox.mo')):
            LANGUAGES[lang] = gettext.translation('gearbox', localedir=CFG['path']['locale'], languages=[lang])


def is_valid(name):
    """Check if a name matches `[a-z][a-z_.0-9]*`."""
    return VALID_NAME.match(name) is not None


def pretty(items, formatting='%s', final='and'):
    """Prettify a list of strings.

    items:      list of strings to be displayed
    formatting: formatting string to apply to each string, must contain "%s"
    final:      linking word of two last strings, typically "and" or "or", should be localized"""
    if not items:
        return ''
    elif len(items) == 1:
        return formatting % items[0]
    else:
        formatted = [formatting % item for item in items]
        return f'%s {final} %s' % (', '.join(formatted[:-1]), formatted[-1])


def has_prefix(text, prefixes=(';',)):
    """Tell if a string has a prefix."""
    for prefix in prefixes:
        if text.startswith(prefix):
            return True
    return False


def strip_prefix(text, prefixes=(';',)):
    """Strip prefixes from a string."""
    for prefix in prefixes:
        if text.startswith(prefix):
            return text[len(prefix):].lstrip()
    return text


def read_commands(text, prefixes, breaker, is_private=False):
    """Read commands from a string, returns the commands and whether or not the command is the only text.

    ";example" will return (['example'], True) because the message is only a command
    "Give an |;example" will return (['example'], False) because the message has other information"""
    if is_private:  # Any private message is considered a command
        return [strip_prefix(text)], True
    if has_prefix(text, prefixes):  # Regular commands
        return [strip_prefix(text, prefixes)], True
    # Here comes the tricky part about the "breaker" character:
    # Users can type things like `please say |;hi` and that'll call `;hi`
    # It's also `possible to ||;say things with a | in them` if you use `||`
    # More info in the readme, but here's the code to parse this
    index = text.find(breaker*2)
    if index >= 0:  # If we have a `||` in the text
        commands = read_commands(text[:index].rstrip(), prefixes, breaker)[0]  # We parse what's before it
        sub = text[index+2:].lstrip()
        if has_prefix(sub, prefixes):  # If there's a command after it, we add it
            commands.append(strip_prefix(sub, prefixes))
        return commands, False
    elif breaker in text:  # If we have a `|`
        commands = []
        for part in text.split(breaker):  # For each part of the message, we check for a command
            if has_prefix(part.strip(), prefixes):
                commands.append(strip_prefix(part.strip(), prefixes))
        return commands, False
    return [], False  # No command was found


def duplicate_command_message(command, matches, language):
    """Simple function returning a localized message for core.py (didn't want a separate translation file)."""
    _ = (lambda s: s) if language not in LANGUAGES else LANGUAGES[language].gettext
    return _('The command `{command}` was found in multiple cogs: {matches}. Use <cog>.{command} to specify.').format(
        command=command, matches=pretty([m[0] for m in matches], '`%s`', final=_('and')))


def str_to_chan(guild, channel):
    """Returns a channel object, given a channel name, ID or <#ID>"""
    id = None
    if re.match('[0-9]{18}', channel):
        id = channel
    elif re.match('<#[0-9]{18}>', channel):
        id = channel[2:-1]
    matches = []
    for chan in guild.channels:
        if chan.id == id:
            return chan
        if channel.lower() in chan.name.lower():
            matches.append(chan)
    if len(matches) == 1:
        return matches[0]
    else:  # No matches, or too general
        return None


def infer_arguments(given, client=None, _cogs=None):
    """Return a list of arguments extracted from data."""
    sent = {}
    # Handle the before/after arguments for update events
    for i, arg1 in enumerate(given):
        for j, arg2 in enumerate(given):
            if type(arg1) == type(arg2) and i < j:
                sent['before'] = arg1
                sent['after'] = arg2
    # Handle the rest of special arguments
    special = {}
    for arg in given:
        for arg_type, arg_name in SPECIAL_TYPES.items():
            if isinstance(arg, arg_type):
                special[arg_name] = arg
    sent['client'] = client
    if 'reaction' in special:
        sent['reaction'] = special['reaction']
    if 'message' in special:
        sent['message'] = special['message']
    elif 'reaction' in special:
        sent['message'] = special['reaction'].message
    if 'message' in sent:
        sent['author'] = sent['message'].author
        sent['content'] = sent['message'].content
    if 'guild_channel' in special:
        sent['guild_channel'] = special['guild_channel']
        sent['channel'] = special['guild_channel']
    elif 'private_channel' in special:
        sent['private_channel'] = special['private_channel']
        sent['channel'] = special['private_channel']
    elif 'message' in sent:
        sent['channel'] = sent['message'].channel
    if 'member' in special:
        sent['member'] = special['member']
    elif 'author' in sent and isinstance(sent['author'], discord.Member):
        sent['member'] = sent['author']
    if 'user' in special:
        sent['user'] = special['user']
    elif 'member' in sent:
        sent['user'] = sent['member']
    elif 'author' in sent:
        sent['user'] = sent['author']
    if 'guild' in special:
        sent['guild'] = special['guild']
    elif 'message' in sent:
        sent['guild'] = sent['message'].guild
    elif 'guild_channel' in sent:
        sent['guild'] = sent['guild_channel'].guild
    elif 'member' in sent:
        sent['guild'] = sent['member'].guild
    if 'guild' in sent:
        if 'channel' in sent and isinstance(sent['channel'], discord.abc.PrivateChannel):
            sent['guild_ex'] = client.get_guild_ex(sent['channel'].id)
        else:
            sent['guild_ex'] = client.get_guild_ex(sent['guild'].id)
    if 'channel' in sent and 'member' in sent:
        sent['permissions'] = sent['channel'].permissions_for(sent['member'])
    sent['flags'] = ''
    sent['__cogs'] = _cogs
    return sent


class Callable:
    """Wrapper of commodity methods common to callable objects."""

    def __init__(self, func):
        self.func = func
        # Argument list
        self.args = list(inspect.signature(func).parameters)
        # Whether or not the function is a coroutine (and shall be awaited)
        self.is_coroutine = inspect.iscoroutinefunction(func)

    def get_arguments(self, given, client=None, *, inferred=None):
        """Rearrange arguments to be passed directly to the callable."""
        if inferred is None:
            inferred = infer_arguments(given, client=client)
        index = 0
        result = []
        for arg in self.args:
            if arg in inferred:
                result.append(inferred.get(arg))
            else:
                result.append(given[index])
                index += 1
        return result

    async def exec(self, client, channel=None, *args, **kwargs):
        """Execute a callable and handles its output."""
        if self.is_coroutine:
            await self.func(*args, **kwargs)
        else:
            output = self.func(*args, **kwargs)
            if output is not None:
                if isinstance(output, discord.Embed):  # If the output is an embed, send it as such
                    await channel.send(embed=output)
                else:
                    try:  # If the output can be casted to a string, send it to Discord
                        output = str(output)
                    except (UnicodeError, UnicodeEncodeError):
                        logging.warning("Unicode error in command '%s' (with arguments %s, %s)",
                                        self.func.__name__, args, kwargs)
                        return
                    if len(output) > 0:
                        await channel.send(str(output))


class Command(Callable):
    """Wrapper for functions considered as commands.

    Contains all information regarding what arguments the command should expect,
    permissions, documentation and such."""

    # Constant for the command behaviour regarding arguments overflow
    FIXED_COUNT = 0  # Fixed argument count, throw error
    FULL_TEXT = 1  # Expecting a string with possible spaces as last argument, put text as is
    POSITIONAL = 2  # Expecting multiple arguments, send array with them

    def __init__(self, func, flags='', *, fulltext=False, delete_message=False, permissions=None,
                 parent=None, fallback=None):
        """Initialize."""
        super().__init__(func)
        # Command arguments as expected by the actual function
        self.params = inspect.signature(func).parameters
        # Command arguments as received from the message
        self.arguments = [arg for arg in self.params if arg not in SPECIAL_ARGS]
        if self.arguments and self.params[self.arguments[-1]].kind.name is 'VAR_POSITIONAL':
            self.last_arg_mode = Command.POSITIONAL
        elif fulltext:
            self.last_arg_mode = Command.FULL_TEXT
        else:
            self.last_arg_mode = Command.FIXED_COUNT
        # Possible flags for the command
        # If `flags` is a string, convert to a dict with empty docstrings
        self.flags = {c: '' for c in flags} if isinstance(flags, str) else flags
        # Minimum argument count
        self.min_arg = len([arg for arg, val in self.params.items()
                            if arg not in SPECIAL_ARGS and isinstance(val.default, type) and
                            self.params[arg].kind.name is not 'VAR_POSITIONAL'])
        # Permissions, can be indicated as a string, (string, bool) tuple, or array of any
        # Ends up being stored as an array of (string, bool) tuples
        self.permissions = []
        if permissions is not None:
            if isinstance(permissions, str):  # consider a single string as a requirement for that permission
                self.permissions.append((permissions, True))
            elif isinstance(permissions, tuple):
                self.permissions.append(permissions)
            elif isinstance(permissions, list):
                self.permissions.extend([(perm, True) if isinstance(perm, str) else perm for perm in permissions])
        # Python argument annotations (aka Type Hints)
        # Can be a docstring, a type hint, or a tuple of both (in any order)
        # A type hint can be either a type, or a `re` pattern (then it is considered a regex that
        # the argument must match), or a set of strings (then the argument must be one of those)
        # See more in the doc/cogs.md file, in the section "Type annotations"
        # argument_name:(type, docstring) mapping of annotations
        self.annotations = {arg: (None, '') for arg in self.arguments}
        # List of types accepted as type hints
        type_types = (type, type(re.compile('')), set)
        for key, item in func.__annotations__.items():
            if key in self.arguments:
                if isinstance(item, str):  # No type hint if there's only a docstring
                    self.annotations[key] = (None, item)
                elif any([isinstance(item, t) for t in type_types]):  # Empty docstring if there's only a type hint
                    self.annotations[key] = (item, '')
                elif isinstance(item, tuple):  # If both are present, check in which order
                    if isinstance(item[0], str) and any([isinstance(item[1], t) for t in type_types]):
                        self.annotations[key] = (item[1], item[0])
                    elif any([isinstance(item[0], t) for t in type_types]) and isinstance(item[1], str):
                        self.annotations[key] = item
                    else:  # Warning in case the annotation is a tuple, but of invalid type
                        logging.warning("Invalid annotation tuple for argument %s in function %s", key, func.__name__)
                else:
                    logging.warning("Invalid annotation type for argument %s in function %s", key, func.__name__)
        # Generate empty docstring if none is present
        if not func.__doc__:
            func.__doc__ = ' '
        # Whether the message should be deleted after command execution (only for single-command messages)
        self.delete_message = delete_message
        # Function to be called
        self.func = func
        # Parent cog
        self.parent = parent
        # In case of denied permission, name of the fallback command - must be a string
        self.fallback = fallback

    def allows(self, permissions):
        """Determine if a command can be called by someone having certain permissions."""
        if permissions is None or self.permissions is None:
            return True
        return all([permission in permissions for permission in self.permissions])

    async def call(self, client, message, arguments, _cogs=None):
        """Call a command."""
        # Compute values of special arguments
        special_args = infer_arguments((message,), client, _cogs)
        assert [arg in SPECIAL_ARGS for arg in special_args] and [arg in special_args for arg in SPECIAL_ARGS]
        # Get translation function for error messages, according to guild settings
        language = special_args['guild_ex'].config['language']
        _ = (lambda s: s) if language not in LANGUAGES else LANGUAGES[language].gettext
        # Strip flags from the list of arguments
        while arguments.startswith('-') and self.flags:
            for flag in arguments.split(' ')[0][1:]:
                if flag != '-':
                    if flag not in self.flags:
                        await message.channel.send(_('Invalid flag: -{flag}').format(flag=flag))
                        return
                    special_args['flags'] += flag
            arguments = arguments[arguments.find(' ') + 1:] if ' ' in arguments else ''
        # Extract arguments from message
        pos_args = []  # Positional arguments, none by default
        args = {key: value for key, value in special_args.items() if key in self.params}
        max_args = len(self.arguments)
        text = arguments.split(None, max_args - 1)
        # Display errors in case of invalid argument count
        if len(text) < self.min_arg:
            await message.channel.send(_('Too few arguments, at least {min_arg_count} expected')
                                       .format(min_arg_count=self.min_arg))
            return
        if len(text) > max_args or (self.last_arg_mode == Command.FIXED_COUNT and len(text) > 0 and ' ' in text[-1]):
            if max_args == 0:
                await message.channel.send(_("This command doesn't expect any arguments"))
            else:
                await message.channel.send(_('Too many arguments, at most {max_arg_count} expected')
                                           .format(max_arg_count=max_args))
            return
        # If positional arguments are expected, store them
        if len(text) == max_args and self.last_arg_mode == Command.POSITIONAL:
            pos_args = text[-1].split()
            text = text[:-1]
        # Type checking code
        temp_args = {key: text[i] for i, key in enumerate(self.arguments) if i < len(text)}
        for key, arg in temp_args.items():
            argtype = self.annotations[key][0]
            # Check type for all annotated parameters, unless positional
            if argtype is not None and not(self.last_arg_mode == Command.POSITIONAL and self.arguments[-1] == key):
                if isinstance(argtype, type):  # If a certain type is expected, cast to it
                    try:
                        if argtype is bool:  # Custom casting for booleans
                            if arg.lower() not in ('true', 'yes', '1', 'false', 'no', '0'):
                                raise ValueError
                            temp_args[key] = arg.lower() in ('true', 'yes', '1')
                        else:  # Regular casting for all other types
                            temp_args[key] = self.annotations[key][0](arg)
                    except ValueError:
                        await message.channel.send(_('Argument "{arg}" should be of type {typename}').format(
                                                     arg=arg, typename=argtype.__name__))
                        return
                elif isinstance(argtype, set):  # Checking if the argument has one of the required values
                    if arg.lower() not in {value.lower() for value in argtype}:  # Name doesn't match (case insensitive)
                        await message.channel.send(_('Argument "{arg}" should have one of the following values: {values}').format(
                                                     arg=arg, values=pretty(argtype, '`%s`', _('or'))))
                        return
                    elif arg not in argtype:  # If only the case isn't matching, convert to expected case
                        for value in argtype:
                            if arg.lower() == value.lower():
                                temp_args[key] = value
                                break
                else:  # argtype is re.compile
                    if argtype.match(arg) is None:  # Checking that the argument matches the expected pattern
                        await message.channel.send(_('Argument "{arg}" should match the following regex: `{pattern}`').format(
                                                     arg=arg, pattern=argtype.pattern))
                        return
        # Update after type checking
        args.update(temp_args)
        # Sort arguments into expected order
        ordered_args = [args[key] for key in self.params if key in args]
        ordered_args += pos_args
        # Update language settings for parent cog (localization)
        self.parent.set_lang(special_args['guild_ex'].config['language'])
        await self.exec(client, message.channel, *ordered_args)


class Event(Callable):
    """Wrapper for cog event handlers."""
    def __init__(self, func):
        super().__init__(func)

    def call(self, client, args, inferred, channel=None):
        if channel is None and 'channel' in inferred:
            channel = inferred['channel']
        return self.exec(client, channel, *self.get_arguments(args, client=client, inferred=inferred))


class Cog:
    """Cog class, containing commands, settings and such.

    Contains the decorators required to declare a function."""

    def __init__(self, name=None, *, config=None):
        """Initialize."""
        # Functions (not commands!) to be called when cog is loaded/unloaded (typically bot startup/shutdown)
        self.on_init = lambda: None
        self.on_exit = lambda: None
        # name:module mapping of sub-cogs
        self.subcogs = {}
        # parent cog if any
        self.parent = None
        # name:Command mapping of commands
        self.commands = {}
        # name:function mapping of events
        self.events = {}
        # alias:name mapping of aliases, contains name:name
        self.aliases = {}
        # list of names which should not be displayed
        self.hidden = []
        # cog name
        self.name = name
        # cog configuration
        self.config = {}
        # config file type, currently either json or yaml
        self.config_type = config
        # language_code:translation mapping of available languages for this cog
        self.languages = {}
        # current language
        self.lang = None
        # bytestring:commands(array) mapping of which commands should be called when receiving specific data
        self.socket_data = {}

    def _get_cfg(self):
        """Return a (module, str) tuple containing the config loader and the config file path."""
        if self.config_type is None:
            return None, None
        module = CONFIG_LOADERS.get(self.config_type)
        path = CFG['path']['config'] % (self.name, self.config_type)
        if module is None:
            logging.warning("Unsupported configuration format '%s' for cog '%s'", self.config_type, self.name)
        return module, path

    def load_cfg(self):  # Called before cog init
        """Read the cog's config from its config file (in the specified format)."""
        # Update the language:translation mapping accordingly
        available_languages = [lang for lang in os.listdir(CFG['path']['locale'])
                               if os.path.isfile(os.path.join(CFG['path']['locale'], lang,
                                                              'LC_MESSAGES', *self.name.split('.')) + '.mo')]
        self.languages = {lang: gettext.translation(os.path.join(*self.name.split('.')),
                                                    localedir=CFG['path']['locale'], languages=[lang])
                          for lang in available_languages}
        self.set_lang('en')
        # Get config loader and path, and read the file
        module, path = self._get_cfg()
        if module is not None:
            try:
                self.config = module.load(open(path))
            except FileNotFoundError:
                logging.warning("No config file at %s for cog %s", path, self.name)

    def save_cfg(self):  # Called after cog exit
        """Write the cog's config to its config file (in the specified format)."""
        module, path = self._get_cfg()
        if module is not None:
            module.dump(self.config, open(path, 'w'))

    def init(self, func):  # Decorator
        """Define a function to call upon loading."""
        self.on_init = func

    def exit(self, func):  # Decorator
        """Define a function to call upon exiting."""
        self.on_exit = func

    def on_socket(self, data):  # Decorator
        """Mark a function to be awaited when specific data is received through websockets.

        The function will be called whenever the data received starts with the specified data,
        which must be a bytestring. The function will be called with (client, truncated data, socket)."""
        def decorator(function):
            if data not in self.socket_data:
                self.socket_data[data] = []
            self.socket_data[data].append(function)
            return function
        return decorator

    async def on_socket_data(self, client, data, socket):  # Called by core
        """Propagate the websocket data to functions."""
        for start_data, commands in self.socket_data.items():
            if isinstance(data, str):  # If the websocket somehow sent a string, then okay (make sure to deal with it)
                start_data = start_data.decode('utf-8')
            if data.startswith(start_data):
                for func in commands:
                    await func(client, data[len(start_data):], socket)

    def hide(self, function=None):  # Decorator
        """Hide a command."""
        def decorate(func):
            self.hidden.append(func.__name__)
            return func
        return decorate(function) if function is not None else decorate

    def alias(self, *aliases):
        """Add aliases to a command."""
        def decorate(func):
            for alias in aliases:
                if is_valid(alias):
                    if alias not in self.aliases:
                        if func.__name__ in self.commands and isinstance(self.commands[func.__name__], str):
                            self.aliases[alias] = self.commands[func.__name__]
                        else:
                            self.aliases[alias] = func.__name__
                    else:
                        logging.error("Couldn't register alias '%s' for '%s': already mapped to '%s'",
                                      alias, func.__name__, self.aliases[alias])
                else:
                    logging.error("Invalid alias name: '%s'", alias)
            return func
        return decorate

    def rename(self, name):
        """Rename a command."""
        def decorate(func):
            if not is_valid(name):
                logging.error("Couldn't rename '%s' to '%s': invalid name", func.__name__, name)
            elif name in self.commands:
                logging.error("Couldn't rename '%s' to '%s': command already existing", func.__name__, name)
            else:
                if name in self.aliases:
                    logging.warning("Command '%s' overwrites an alias mapped to '%s'", name, self.aliases[name])
                self.aliases[name] = name
                for alias, dest in self.aliases.items():
                    if dest == func.__name__:
                        self.aliases[alias] = name
                self.commands[func.__name__] = name
            return func
        return decorate

    def event(self, func):
        """Decorator used to declare an event."""
        name = func.__name__
        self.events[name] = Event(func)
        return func

    def command(self, func=None, **kwargs):
        """Decorator used to declare a command.

        See Command.__init__ for documentation about the keyword arguments."""
        def decorator(function):
            name = function.__name__
            if name in self.commands:
                real_name = self.commands[name]
                self.commands.pop(name)
                name = real_name
            else:
                if not is_valid(name):
                    logging.critical("Invalid command name '%s' in module '%s'", name, self.name)
                    return lambda *a, **kw: None
                if name in self.aliases:
                    logging.warning("Command '%s' overwrites an alias mapped to '%s'", name, self.aliases[name])
                self.aliases[name] = name
            self.commands[name] = Command(function, parent=self, **kwargs)
            return function
        return decorator if func is None else decorator(func)

    def has(self, name, permissions=None):
        """Check if a cog has a command."""
        if name not in self.aliases:
            return False
        if permissions is None:
            return True
        return self.get(name, permissions) is not None

    def get(self, name, permissions=None):
        """Return the command needed."""
        if name in self.aliases:
            command = self.commands.get(self.aliases[name])
            if permissions is None or command.allows(permissions):
                return command
            if command.fallback is not None:
                return self.get(command.fallback, permissions)
            return None

    def get_all(self, permissions=None):
        """Return all commands available for certain permissions, as a dictionary."""
        if permissions is None:
            return self.commands
        return {name: self.get(name, permissions) for name, command in self.commands.items()
                if self.has(name, permissions) and name not in self.hidden}

    def set_lang(self, lang):
        """Change the current language. Used for per-guild localization."""
        self.lang = self.languages.get(lang, None)

    def gettext(self, text):
        """`gettext` wrapper for the current language."""
        if self.lang is None:
            return text
        return self.lang.gettext(text)

    def ngettext(self, singular, plural, n):
        """`ngettext` wrapper for the current language."""
        if self.lang is None:
            if n == 1:
                return singular
            return plural
        return self.lang.ngettext(singular, plural, n)


class Guild:
    """Custom guild class, used to store additional information."""
    default_cfg = {'cogs': {'blacklist': []}, 'language': 'en', 'timezone': 'UTC', 'prefixes': [';'], 'breaker': '|'}

    def __init__(self, sid, path):
        """Initialize."""
        self.id = sid
        self.path = path % sid
        self.config = None
        self.blacklist = None
        self.prefixes = None
        self.load()

    def is_allowed(self, cog_name):
        """Whether or not a cog can be used on the guild."""
        if cog_name in self.blacklist:
            return False
        if any([cog_name.startswith(parent + '.') for parent in self.blacklist]):
            return False
        return True

    def load(self):
        """Load guild-specific configuration file, create default if non-existent."""
        try:
            self.config = {}
            self.config.update(Guild.default_cfg)
            config.merge(self.config, json.load(open(self.path)))
        except FileNotFoundError:
            self.config = Guild.default_cfg
            self._write()
        self.blacklist = self.config['cogs']['blacklist']
        self.prefixes = self.config['prefixes']

    def write(self):
        """Write guild-specific configuration file."""
        self.config['cogs']['blacklist'] = self.blacklist
        self.config['prefixes'] = self.prefixes
        self._write()

    def _write(self):
        json.dump(self.config, open(self.path, 'w'))
