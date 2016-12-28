"""More like a toolbox, actually."""
import inspect
import logging
import os
import re
import json
import yaml
import config
import gettext


version = 'unknown'
version_is_dev = False
SPECIAL_ARGS = ('message', 'author', 'channel', 'server', 'server_ex', 'client', 'flags', '__cogs', 'permissions')
VALID_NAME = re.compile('[a-z][a-z_.0-9]*$')
CONFIG_LOADERS = {'json': json, 'yaml': yaml}
CFG = {}
LANGUAGES = {}


def update_config(cfg):
    global version, version_is_dev, LANGUAGES
    CFG.update(cfg)
    version_path = CFG['path']['version']
    try:
        ver_num, ver_type = open(version_path).read().strip().split()
        version = ver_num
        version_is_dev = ver_type == 'dev'
    except ValueError:
        logging.warning('Wrong version file format! It should be <number> <type>')
    except FileNotFoundError:
        logging.warning('Version file %s not found' % version_path)
    except EnvironmentError as exc:
        logging.warning("Couldn't open version file '%s': %s", version_path, exc)
    for lang in os.listdir(CFG['path']['locale']):
        if os.path.isfile(os.path.join(CFG['path']['locale'], lang, 'LC_MESSAGES', 'gearbox.mo')):
            LANGUAGES[lang] = gettext.translation('gearbox', localedir=CFG['path']['locale'], languages=[lang])


def is_valid(name):
    """Check if a name matches `[a-z][a-z_0-9]*`."""
    return VALID_NAME.match(name) is not None


def pretty(items, formatting='%s', final='and'):
    """Prettify a list of strings."""
    if not items:
        return ''
    elif len(items) == 1:
        return formatting % items[0]
    else:
        formatted = [formatting % item for item in items]
        return f'%s {final} %s' % (', '.join(formatted[:-1]), formatted[-1])


def has_prefix(text, prefixes=';'):
    """Tell if a string has a prefix."""
    for prefix in prefixes:
        if text.startswith(prefix):
            return True
    return False


def strip_prefix(text, prefixes=';'):
    """Strip prefixes from a string."""
    for prefix in prefixes:
        if text.startswith(prefix):
            return text[len(prefix):].lstrip()
    return text


def read_commands(text, prefixes, breaker, is_private=False):
    """Read commands from a string, returns the commands and whether or not the command is the only text.

    ";example" will return (['example'], True) because the message is only a command
    "Give an |;example" will return (['example'], False) because the message has other information"""
    if is_private: # Any private message is considered a command
        return strip_prefix(text), True
    if has_prefix(text, prefixes): # Regular commands
        return [strip_prefix(text, prefixes)], True
    # Here comes the tricky part about the "breaker" character:
    # Users can type things like `please say |;hi` and that'll call `;hi`
    # It's also `possible to ||;say things with a | in them` if you use `||`
    # More info in the readme, but here's the code to parse this
    index = text.find(breaker*2)
    if index >= 0:  # If we have a `||` in the text
        commands = read_commands(text[:index].rstrip(), prefixes, breaker)[0] # We parse what's before it
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
    return (), False  # No command was found


def duplicate_command_message(command, matches, language):
    _ = (lambda s: s) if language not in LANGUAGES else LANGUAGES[language].gettext
    return _('The command `{command}` was found in multiple cogs: {matches}. Use <cog>.{command} to specify.').format(
        command=command, matches=pretty([m[0] for m in matches], '`%s`', final=_('and')))


class Command:
    """Guess what."""

    FIXED_COUNT = 0
    FULL_TEXT = 1
    POSITIONAL = 2

    def __init__(self, func, flags='', *, fulltext=False, delete_message=False, permissions=None,
                 parent=None, fallback=None):
        """Guess."""
        self.params = inspect.signature(func).parameters
        # self.special = [arg for arg in params if arg in SPECIAL_ARGS]
        self.normal = [arg for arg in self.params if arg not in SPECIAL_ARGS]
        if self.normal and self.params[self.normal[-1]].kind.name is 'VAR_POSITIONAL':
            self.last_arg_mode = Command.POSITIONAL
        elif fulltext:
            self.last_arg_mode = Command.FULL_TEXT
        else:
            self.last_arg_mode = Command.FIXED_COUNT
        self.flags = {c: '' for c in flags} if type(flags) is str else flags
        self.delete_message = delete_message
        self.min_arg = len([arg for arg, val in self.params.items()
                            if arg not in SPECIAL_ARGS and isinstance(val.default, type)
                            and self.params[arg].kind.name is not 'VAR_POSITIONAL'])
        self.iscoroutine = inspect.iscoroutinefunction(func)
        self.func = func
        self.permissions = []
        if permissions is not None:
            if type(permissions) is str:
                self.permissions.append((permissions, True))
            elif type(permissions) is tuple:
                self.permissions.append(permissions)
            elif type(permissions) is list:
                self.permissions.extend([(perm, True) if type(perm) is str else perm for perm in permissions])
        self.annotations = {arg: (None, '') for arg in self.normal}
        type_types = (type, type(re.compile('')), set)
        for key, item in func.__annotations__.items():
            if key in self.normal:
                if type(item) is str:
                    self.annotations[key] = (None, item)
                elif type(item) in type_types:
                    self.annotations[key] = (item, '')
                elif type(item) is tuple:
                    if type(item[0]) is str and type(item[1]) in type_types:
                        self.annotations[key] = (item[1], item[0])
                    elif type(item[0]) in type_types and type(item[1]) is str:
                        self.annotations[key] = item
        if not func.__doc__:
            func.__doc__ = ' '
        self.parent = parent
        self.fallback = fallback

    def allows(self, permissions):
        """Determine if a command can be called by someone having certain permissions."""
        if permissions is None or self.permissions is None:
            return True
        return all([permission in permissions for permission in self.permissions])

    async def call(self, client, message, arguments, _cogs=None):
        """Call a command."""
        special_args = {'client': client, 'message': message, 'author': message.author,
                        'channel': message.channel, 'server': message.server,
                        'server_ex': client.servers_ex[message.channel.id if message.channel.is_private else
                                                       message.server.id], 'flags': '', '__cogs': _cogs,
                        'permissions': message.channel.permissions_for(message.author)}
        language = special_args['server_ex'].config['language']
        _ = (lambda s: s) if language not in LANGUAGES else LANGUAGES[language].gettext
        while arguments.startswith('-') and self.flags:
            for flag in arguments.split(' ')[0][1:]:
                if flag != '-':
                    if flag not in self.flags:
                        await client.send_message(message.channel, _('Invalid flag: -{flag}').format(flag=flag))
                        return
                    special_args['flags'] += flag
            arguments = arguments[arguments.find(' ') + 1:] if ' ' in arguments else ''
        pos_args = []
        args = {key: value for key, value in special_args.items() if key in self.params}
        max_args = len(self.normal)
        text = arguments.split(' ', max_args - 1)
        text = [arg for arg in text if len(arg) > 0]
        if len(text) < self.min_arg:
            await client.send_message(message.channel, _('Too few arguments, at least {min_arg_count} expected')
                                      .format(min_arg_count=self.min_arg))
            return None
        if len(text) > max_args or (self.last_arg_mode == Command.FIXED_COUNT and len(text) > 0 and ' ' in text[-1]):
            await client.send_message(message.channel, _('Too many arguments, at most {max_arg_count} expected')
                                      .format(max_arg_count=max_args))
            return None
        if len(text) == max_args and self.last_arg_mode == Command.POSITIONAL:
            pos_args = text[-1].split()
            text = text[:-1]
        temp_args = {key: text[i] for i, key in enumerate(self.normal) if i < len(text)}
        for key, arg in temp_args.items():
            argtype = self.annotations[key][0]
            if argtype is not None and not(self.last_arg_mode == Command.POSITIONAL and self.normal[-1] == key):
                if type(argtype) is type:
                    try:
                        if argtype is bool:
                            if arg.lower() not in ('true', 'yes', '1', 'false', 'no', '0'):
                                raise ValueError
                            temp_args[key] = arg.lower() in ('true', 'yes', '1')
                        else:
                            temp_args[key] = self.annotations[key][0](arg)
                    except ValueError:
                        await client.send_message(message.channel,
                                                  _('Argument "{arg}" should be of type {typename}').format(
                                                      arg=arg, typename=argtype.__name__))
                        return None
                elif type(argtype) is set:
                    if arg.lower() not in {value.lower() for value in argtype}:  # Name doesn't match (case insensitive)
                        await client.send_message(message.channel,
                                                  _('Argument "{arg}" should have one of the following values: {values}').format(
                                                    arg=arg, values=pretty(argtype, '`%s`', _('or'))))
                        return None
                    elif arg not in argtype:  # Name matching but wrong case
                        for value in argtype:
                            if arg.lower() == value.lower():
                                temp_args[key] = value
                                break
                else:  # argtype is re.compile
                    if argtype.match(arg) is None:
                        await client.send_message(message.channel,
                                                  _('Argument "{arg}" should match the following regex: `{pattern}`').format(
                                                    arg=arg, pattern=argtype.pattern))
                        return None
        args.update(temp_args)
        # if self.multiple:
        #     args = args[:-1] + text[len(self.normal) - 1:]
        # elif self.normal:
        #     args[-1] = ' '.join(text[len(self.normal) - 1:])
        ordered_args = [args[key] for key in self.params if key in args]
        ordered_args += pos_args
        self.parent.set_lang(special_args['server_ex'].config['language'])
        if self.iscoroutine:
            output = await self.func(*ordered_args)
        else:
            output = self.func(*ordered_args)
        if output is not None:
            try:
                output = str(output)
            except (UnicodeError, UnicodeEncodeError):
                logging.warning("Unicode error in command '%s' (with arguments %s)",
                                self.func.__name__, ordered_args)
                return
            if len(output) > 0:
                await client.send_message(message.channel, str(output))


class Cog:
    """The cog class containing the decorators."""

    def __init__(self, name=None, *, config=None):
        """Initialization."""
        self.on_init = lambda: None
        self.on_exit = lambda: None
        self.subcogs = {}
        self.commands = {}
        self.aliases = {}
        self.hidden = []
        self.name = name
        self.react = {}
        self.config = {}
        self.config_type = config
        self.languages = {}
        self.lang = None

    def _get_cfg(self):
        if self.config_type is None:
            return None, None
        module = CONFIG_LOADERS.get(self.config_type)
        path = CFG['path']['config'] % (self.name, self.config_type)
        if module is None:
            logging.warning("Unsupported configuration format '%s' for cog '%s'", self.config_type, self.name)
        return module, path

    def load_cfg(self):
        available_languages = [lang for lang in os.listdir(CFG['path']['locale'])
                               if os.path.isfile(os.path.join(CFG['path']['locale'], lang,
                                                              'LC_MESSAGES', *self.name.split('.')) + '.mo')]
        self.languages = {lang: gettext.translation(os.path.join(*self.name.split('.')),
                                                    localedir=CFG['path']['locale'], languages=[lang])
                          for lang in available_languages}
        self.set_lang('en')
        module, path = self._get_cfg()
        if module is not None:
            try:
                self.config = module.load(open(path))
            except FileNotFoundError:
                logging.warning("No config file at %s for cog %s", path, self.name)

    def save_cfg(self):
        module, path = self._get_cfg()
        if module is not None:
            module.dump(self.config, open(path, 'w'))

    def init(self, func):
        """Define a function to call upon loading."""
        self.on_init = func

    def exit(self, func):
        """Define a function to call upon exiting."""
        self.on_exit = func

    def on_reaction(self, arg):
        func = None
        if type(arg) is str:
            arg = (arg,)
        elif type(arg) is not tuple:
            func = arg
            arg = (0,)

        def decorator(function):
            for a in arg:
                if a not in self.react:
                    self.react[a] = []
                self.react[a].append(function)
            return function
        return decorator if func is None else decorator(func)

    async def on_reaction_any(self, client, added, reaction, user):
        calls = self.react.get(0, [])
        calls.extend(self.react.get(reaction.emoji.id if reaction.custom_emoji else reaction.emoji, []))
        for func in calls:
            await func(client, added, reaction, user)

    def hide(self, function=None):
        """Hide a command."""
        def decorate(func):
            self.hidden.append(func.__name__)
            return func
        return decorate(function) if function is not None else decorate

    def alias(self, *aliases):
        """Add aliases to a command."""
        def decorate(func):
            """Decorator to add an alias."""
            for alias in aliases:
                if is_valid(alias):
                    if alias not in self.aliases:
                        if func.__name__ in self.commands and type(self.commands[func.__name__]) is str:
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
            """Decorator to rename."""
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

    def command(self, func=None, **kwargs):
        """Command decorator."""
        def decorator(function):
            """Command decorator."""
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
        self.lang = self.languages.get(lang, None)

    def gettext(self, text):
        if self.lang is None:
            return text
        return self.lang.gettext(text)

    def ngettext(self, singular, plural, n):
        if self.lang is None:
            if n == 1:
                return singular
            return plural
        return self.lang.ngettext(singular, plural, n)


class Server:
    """Custom server class."""
    default_cfg = {'cogs': {'blacklist': []}, 'language': 'en', 'prefixes': [';'], 'breaker': '|'}

    def __init__(self, sid, path):
        """Initialize."""
        self.id = sid
        self.path = path % sid
        self.config = None
        self.blacklist = None
        self.prefixes = None
        self.load()

    def is_allowed(self, cog_name):
        if cog_name in self.blacklist:
            return False
        if any([cog_name.startswith(parent + '.') for parent in self.blacklist]):
            return False
        return True

    def load(self):
        try:
            self.config = {}
            self.config.update(Server.default_cfg)
            config.merge(self.config, json.load(open(self.path)))
        except FileNotFoundError:
            self.config = Server.default_cfg
            self._write()
        self.blacklist = self.config['cogs']['blacklist']
        self.prefixes = self.config['prefixes']

    def write(self):
        self.config['cogs']['blacklist'] = self.blacklist
        self.config['prefixes'] = self.prefixes
        self._write()

    def _write(self):
        json.dump(self.config, open(self.path, 'w'))
