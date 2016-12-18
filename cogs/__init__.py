"""Importing all cogs."""
COGS = {}       # name:module mapping of properly loaded cogs
FAIL = set()    # names of cogs that failed to load
NO_COG = {}     # name:module mapping of properly loaded cogs that don't have `cog`


def load(name):
    """Load a cog given its name (file name without extension)."""
    import importlib
    import logging
    try:
        if name in NO_COG:  # if the module was properly loaded but didn't have `cog`
            mod = NO_COG.pop(name)
            importlib.reload(mod)
        else:  # regular loading
            mod = importlib.import_module(__name__ + '.' + name)
    except Exception as exc:  # Yes I know it's too general. Just wanna catch 'em all.
        logging.critical("%s while loading '%s': %s", type(exc).__name__, name, exc)
        FAIL.add(name)
        return
    if not hasattr(mod, 'cog'):  # if mod.cog does not exist, cog isn't considered as properly loaded
        logging.critical("Cog '%s' does not have the `cog` variable", name)
        FAIL.add(name)
        NO_COG[name] = mod
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
        else:
            logging.info("Reloaded '%s'.", name)
    mod.cog.load_cfg()
    mod.cog.on_init()
    mod.cog.subcogs = subcogs


def cog(name):
    """Return a Cog object given its name."""
    if name not in COGS:
        return None
    return COGS[name].cog


def command(cmd, server_ex=None):
    """Find a command given its name."""
    allowed = server_ex.is_allowed if server_ex is not None else (lambda _: True)
    matches = []
    for name, _cog in COGS.items():
        if allowed(name) and _cog.cog.has(cmd):
            matches.append((name, _cog.cog.get(cmd)))
    return matches
