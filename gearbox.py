"""More like a toolbox, actually."""
import inspect
import logging
import re


SERVER_CONFIG_PATH = 'servers/%s.json'
SPECIAL_ARGS = ('message', 'author', 'channel', 'server', 'client', 'flags')
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

    def __init__(self, func, fulltext=False, flags='', delete_message=False):
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
        self.flags = flags
        self.delete_message = delete_message
        self.min_arg = len([arg for arg, val in self.params.items() if arg not in SPECIAL_ARGS and isinstance(val.default, type)])
        self.iscoroutine = inspect.iscoroutine(func)
        self.func = func

    async def call(self, client, message, arguments):
        """Call a command."""
        special_args = {'client': client, 'message': message, 'author': message.author,
                        'channel': message.channel, 'server': message.server, 'flags': ''}
        if arguments.startswith('-') and self.flags:
            for flag in arguments.split(' ')[0][1:]:
                if flag not in self.flags:
                    await client.send_message(message.channel, f'Invalid flag: -{flag}')
                    return
                special_args['flags'] += flag
            arguments = arguments[arguments.find(' ') + 1:] if ' ' in arguments else ''
        pos_args = []
        args = {key:value for key, value in special_args.items() if key in self.params}
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
        args.update({key:text[i] for i, key in enumerate(self.normal) if i < len(text)})
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

    def init(self, func):
        """Define a function to call upon loading."""
        self.on_init = func

    def exit(self, func):
        """Define a function to call upon exiting."""
        self.on_exit = func

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
                self.commands[name] = Command(func)
                self.commands.pop(func.__name__)
            return func
        return decorate

    def command(self, func=None, **kwargs):
        """Command decorator."""
        def decorator(func):
            """Command decorator."""
            name = func.__name__
            if not is_valid(name):
                logging.critical("Invalid command name '%s' in module '%s'", name, self.name)
                return lambda *a, **kw: None
            if name in self.aliases:
                logging.warning("Command '%s' overwrites an alias mapped to '%s'", name, self.aliases[name])
            self.aliases[name] = name
            self.commands[name] = Command(func, **kwargs)
            return func
        return decorator if func is None else decorator(func)

    def has(self, name):
        """Check if a cog has a command."""
        return name in self.aliases

    def get(self, name):
        """Return the command needed."""
        if name in self.aliases:
            return self.commands.get(self.aliases[name])
