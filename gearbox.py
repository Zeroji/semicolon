"""More like a toolbox, actually."""
import inspect
import logging
import re
import json


SERVER_CONFIG_PATH = 'servers/%s.json'
SPECIAL_ARGS = ('message', 'author', 'channel', 'server', 'server_ex', 'client', 'flags', '__cogs')
VALID_NAME = re.compile('[a-z][a-z_0-9]*$')


def is_valid(name):
    """Check if a name matches `[a-z][a-z_0-9]*`."""
    return VALID_NAME.match(name) is not None


def pretty(items, formatting='%s'):
    """Prettify a list of strings."""
    if not items:
        return ''
    elif len(items) == 1:
        return formatting % items[0]
    else:
        formatted = [formatting % item for item in items]
        return '%s and %s' % (', '.join(formatted[:-1]), formatted[-1])


def strip_prefix(text, prefixes=';'):
    """Strip prefixes from a string and tell if there were none."""
    # Returns the stripped string, and True if prefixes were stripped.
    for prefix in prefixes:
        if text.startswith(prefix):
            return text[len(prefix):].lstrip(), True
    return text, False


class Command:
    """Guess what."""

    def __init__(self, func, flags='', fulltext=False, delete_message=False, permissions=None):
        """Guess."""
        self.params = inspect.signature(func).parameters
        # self.special = [arg for arg in params if arg in SPECIAL_ARGS]
        self.normal = [arg for arg in self.params if arg not in SPECIAL_ARGS]
        if self.normal and self.params[self.normal[-1]].kind.name is 'VAR_POSITIONAL':
            self.last_arg_mode = 2  # Positional
        elif fulltext:
            self.last_arg_mode = 1  # Full text
        else:
            self.last_arg_mode = 0  # Fixed argument count
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
        type_types = (type, type(re.compile('')))
        for key, item in func.__annotations__.items():
            if key in self.normal:
                if type(item) is str:
                    self.annotations[key] = (None, item)
                elif type(item) in type_types:
                    self.annotations[key] = (item, None)
                elif type(item) is tuple:
                    if type(item[0]) is str and type(item[1]) in type_types:
                        self.annotations[key] = (item[1], item[0])
                    elif type(item[0]) in type_types and type(item[1]) is str:
                        self.annotations[key] = item

    async def call(self, client, message, arguments, _cogs=None):
        """Call a command."""
        special_args = {'client': client, 'message': message, 'author': message.author,
                        'channel': message.channel, 'server': message.server,
                        'server_ex': client.server[message.channel.id if message.channel.is_private else
                                                   message.server.id], 'flags': '', '__cogs': _cogs}
        if arguments.startswith('-') and self.flags:
            for flag in arguments.split(' ')[0][1:]:
                if flag not in self.flags:
                    await client.send_message(message.channel, f'Invalid flag: -{flag}')
                    return
                special_args['flags'] += flag
            arguments = arguments[arguments.find(' ') + 1:] if ' ' in arguments else ''
        pos_args = []
        args = {key: value for key, value in special_args.items() if key in self.params}
        max_args = len(self.normal)
        text = arguments.split(' ', max_args - 1)
        text = [arg for arg in text if len(arg) > 0]
        if (len(text) < self.min_arg or len(text) > max_args or
                (self.last_arg_mode == 0 and len(text) > 0 and ' ' in text[-1])):
            await client.send_message(message.channel, 'Invalid argument count!')
            return None
        if len(text) == max_args and self.last_arg_mode == 2:
            pos_args = text[-1].split()
            text = text[:-1]
        temp_args = {key: text[i] for i, key in enumerate(self.normal) if i < len(text)}
        for key, arg in temp_args.items():
            argtype = self.annotations[key][0]
            if argtype is not None and not(self.last_arg_mode == 2 and self.normal[-1] == key):
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
                                                  f'Argument "{arg}" should be of type `{argtype.__name__}`')
                        return None
                else:  # argtype is re.compile
                    if argtype.match(arg) is None:
                        await client.send_message(message.channel, f'Argument "{arg}" should match '
                                                                   f'the following regex: `{argtype.pattern}`')
                        return None
        args.update(temp_args)
        # if self.multiple:
        #     args = args[:-1] + text[len(self.normal) - 1:]
        # elif self.normal:
        #     args[-1] = ' '.join(text[len(self.normal) - 1:])
        ordered_args = [args[key] for key in self.params if key in args]
        ordered_args += pos_args
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
            else:
                if len(output) > 0:
                    await client.send_message(message.channel, str(output))


class Cog:
    """The cog class containing the decorators."""

    def __init__(self, name=None):
        """Initialization."""
        self.on_init = lambda: None
        self.on_exit = lambda: None
        self.commands = {}
        self.aliases = {}
        self.name = name
        self.react = {}

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

    def alias(self, *aliases):
        """Add aliases to a command."""
        def decorate(func):
            """Decorator to add an alias."""
            for alias in aliases:
                if is_valid(alias):
                    if alias not in self.aliases:
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
            self.commands[name] = Command(function, **kwargs)
            return function
        return decorator if func is None else decorator(func)

    def has(self, name):
        """Check if a cog has a command."""
        return name in self.aliases

    def get(self, name):
        """Return the command needed."""
        if name in self.aliases:
            return self.commands.get(self.aliases[name])


class Server:
    """Custom server class."""

    def __init__(self, sid, path):
        """Initialize."""
        self.id = sid
        self.path = path % sid
        self.config = None
        self.blacklist = None
        self.prefixes = None
        self.load()

    def load(self):
        try:
            self.config = json.load(open(self.path))
        except FileNotFoundError:
            self.config = {'cogs': {'blacklist': []}, 'prefixes': [';']}
            self._write()
        self.blacklist = self.config['cogs']['blacklist']
        self.prefixes = self.config['prefixes']

    def write(self):
        self.config['cogs']['blacklist'] = self.blacklist
        self.config['prefixes'] = self.prefixes
        self._write()

    def _write(self):
        json.dump(self.config, open(self.path, 'w'))
