"""More like a toolbox, actually."""
import inspect
import logging


SERVER_CONFIG_PATH = 'servers/%s.json'
SPECIAL_ARGS = ('message', 'author', 'channel', 'server', 'client')
ALLOWED_CHARS = 'abcdefghijklmnopqrstuvwxyz_0123456789'


def is_valid(name):
    """Check if a name matches [a-z][a-z_0-9]*."""
    if name[:1] in ALLOWED_CHARS[26:]:
        return False
    return all([c in ALLOWED_CHARS for c in name])


def pretty(items, formatting='%s'):
    if not items:
        return ''
    elif len(items) == 1:
        return formatting % items[0]
    else:
        formatted = [formatting % item for item in items]
        return '%s and %s' % (', '.join(formatted[:-1]), formatted[-1])


def strip_prefix(text, prefixes=';'):
    is_command = False
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):].lstrip()
            is_command = True
            break
    return text, is_command


class Command:
    """Guess what."""

    def __init__(self, func):
        """Guess."""
        self.params = inspect.signature(func).parameters
        # self.special = [arg for arg in params if arg in SPECIAL_ARGS]
        self.normal = [arg for arg in self.params if arg not in SPECIAL_ARGS]
        self.multiple = self.normal and self.params[self.normal[-1]].kind.name is 'VAR_POSITIONAL'
        self.iscoroutine = inspect.iscoroutine(func)
        self.func = func

    async def call(self, client, message, arguments):
        """Call a command."""
        special_args = {'client': client, 'message': message, 'author': message.author,
                        'channel': message.channel, 'server': message.server}
        args = []
        kwargs = {key:value for key, value in special_args.items() if key in self.params}
        text = arguments.split()
        kwargs.update({key:(text[i] if i<len(text) else '') for i, key in enumerate(self.normal)})
        args = [kwargs[key] for key in self.params]
        if self.multiple:
            args = args[:-1] + text[len(self.normal) - 1:]
        elif self.normal:
            args[-1] = ' '.join(text[len(self.normal) - 1:])
        if self.iscoroutine:
            await self.func(*args)
        else:
            output = self.func(*args)
            if isinstance(output, str):
                await client.send_message(message.channel, output)


class Cog:
    """The cog class containing the decorators."""

    def __init__(self, name=''):
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

    def command(self, func):
        """Command decorator."""
        name = func.__name__
        if not is_valid(name):
            logging.critical("Invalid command name '%s' in module '%s'", name, self.name)
            return lambda *a, **kw: None
        if name in self.aliases:
            logging.warning("Command '%s' overwrites an alias mapped to '%s'", name, self.aliases[name])
        self.aliases[name] = name
        self.commands[name] = Command(func)
        return func

    def has(self, name):
        """Check if a cog has a command."""
        return name in self.aliases

    def get(self, name):
        """Returns the command needed."""
        if name in self.aliases:
            return self.commands.get(self.aliases[name])
