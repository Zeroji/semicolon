"""Importing all cogs."""


class Wrapper:

    def __init__(self):
        self.cogs = {}       # name:module mapping of properly loaded cogs
        self.fail = set()    # names of cogs that failed to load
        self.no_cog = {}     # name:module mapping of properly loaded cogs that don't have `cog`

    def load(self, name):
        """Load a cog given its name (file name without extension)."""
        import importlib
        import logging
        try:
            if name in self.no_cog:  # if the module was properly loaded but didn't have `cog`
                mod = self.no_cog.pop(name)
                importlib.reload(mod)
            else:  # regular loading
                mod = importlib.import_module(__name__ + '.' + name)
        except Exception as exc:  # Yes I know it's too general. Just wanna catch 'em all.
            logging.critical("%s while loading '%s': %s", type(exc).__name__, name, exc)
            self.fail.add(name)
            return
        if not hasattr(mod, 'cog'):  # if mod.cog does not exist, cog isn't considered as properly loaded
            logging.critical("Cog '%s' does not have the `cog` variable", name)
            self.fail.add(name)
            self.no_cog[name] = mod
            return
        base_name = name[:name.rfind('.') + 1]
        if mod.cog.name is not None:
            name = base_name + mod.cog.name
        else:
            name = base_name + name.rsplit('.', 1)[-1]
        mod.cog.name = name
        mod.cog.load_cfg()
        mod.cog.on_init()
        logging.info("Loaded cog '%s'.", name)
        self.cogs[name] = mod

    def reload(self, name, mod):  # Passing name for logging purposes
        """Reload a cog."""
        import importlib
        import logging
        subcogs = mod.cog.subcogs
        mod.cog.on_exit()
        try:
            importlib.reload(mod)
        except Exception as exc:
            logging.error("%s while reloading '%s': %s", type(exc).__name__, name, exc)
        else:
            if mod.cog.name is None:
                mod.cog.name = name
            if mod.cog.name != name:
                self.cogs[mod.cog.name] = self.cogs.pop(name)
                logging.info("Reloaded '%s' as '%s'.", name, mod.cog.name)
            else:
                logging.info("Reloaded '%s'.", name)
        mod.cog.load_cfg()
        mod.cog.on_init()
        mod.cog.subcogs = subcogs

    def cog(self, name):
        """Return a Cog object given its name."""
        if name not in self.cogs:
            return None
        return self.cogs[name].cog

    def command(self, cmd, guild_ex=None, permissions=None):
        """Find a command given its name."""
        allowed = guild_ex.is_allowed if guild_ex is not None else (lambda _: True)
        matches = []
        for name, _cog in self.cogs.items():
            if allowed(name) and _cog.cog.has(cmd, permissions):
                matches.append((name, _cog.cog.get(cmd, permissions)))
        return matches

    def __iter__(self):
        return [module.cog for module in self.cogs.values()].__iter__()