"""Importing all cogs."""
COGS = {}


def load(name):
    """Load a cog given its name (file name without extension)."""
    import importlib
    import logging
    mod = None
    try:
        mod = importlib.import_module(__name__ + '.' + name)
    except Exception as exc:  # Yes I know it's too general. Just wanna catch 'em all.
        logging.critical("%s while loading '%s': %s", type(exc).__name__, name, exc)
    else:
        base_name = name[:name.rfind('.') + 1]
        mod.cog.on_init()
        if mod.cog.name is not None:
            name = base_name + mod.cog.name
        else:
            name = base_name + name
        mod.cog.name = name
        logging.info("Loaded cog '%s'.", name)
    COGS[name] = mod


def reload(name, mod):  # Passing name for logging purposes
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
            COGS[mod.cog.name] = COGS.pop(name)
            logging.info("Reloaded '%s' as '%s'.", name, mod.cog.name)
            name = mod.cog.name
        else:
            logging.info("Reloaded '%s'.", name)
    mod.cog.on_init()
    mod.cog.subcogs = subcogs


def cog(name):
    """Return a Cog object given its name."""
    if not name in COGS:
        return None
    return COGS[name].cog


def command(cmd, blacklist=None):
    """Find a command given its name."""
    if blacklist is None:
        blacklist = []
    matches = []
    for name, _cog in COGS.items():
        if name not in blacklist and _cog.cog.has(cmd):
            matches.append((name, _cog.cog.get(cmd)))
    return matches
