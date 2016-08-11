"""Importing all cogs."""
COGS = {}

def load(name):
    import importlib
    import logging
    mod = None
    try:
        mod = importlib.import_module(__name__ + '.' + name)
    except Exception as exc:  # Yes I know it's too general. Just wanna catch 'em all.
        logging.critical("Error while loading '%s': %s", name, exc)
    else:
        logging.info("Loaded module '%s'.", name)
    COGS[name] = mod

def cog(name):
    """Returns a Cog object given its name."""
    if not name in COGS:
        return None
    return COGS[name].cog

def command(cmd):
    """Finds a command given its name."""
    matches = []
    for name, _cog in COGS.items():
        if _cog.cog.has(cmd):
            matches.append((name, _cog.cog.get(cmd)))
    if not matches:
        return None
    if len(matches) == 1:
        # Return the Command object
        return matches[0][1]
    else:
        # Return the names of the cogs containing that command
        return [name for name, _ in matches]
