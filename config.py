"""Handle ;;'s config."""
import collections
import yaml.parser


DEFAULT_PATH = 'config.yaml'
DEFAULT_CFG = {
    'path': {
        'log': 'run.log',
        'token': 'data/secret/token',
        'master': 'data/master',
        'admins': 'data/admins',
        'banned': 'data/banned',
        'server': 'data/servers/%s.json',
        'config': 'config/%s.%s',
        'version': 'version',
    }, 'wheel': {
        'import': True,
        'reload': True,
    }
}


def merge(dest, update, *, key_check=False):
    """Recursively update a nested dictionary."""
    # [From StackOverflow](http://stackoverflow.com/a/3233356)
    # Modified to raise ValueError in case of type mismatch, and ignore new keys
    for key, value in update.items():
        if key_check:
            if key not in dest:
                print(f"Useless key '{key}' with value '{value}'")
                continue
            if not isinstance(value, type(dest[key])):
                raise ValueError(f"Type mismatch on key '{key}'")
        if isinstance(value, collections.Mapping):
            temp = merge(dest.get(key, {}), value, key_check=key_check)
            dest[key] = temp
        else:
            dest[key] = update[key]
    return dest


def load(given_path, config):
    """Load config from file or default."""
    path = given_path or DEFAULT_PATH

    try:
        config_file = open(path, mode='r')
    except FileNotFoundError:
        if given_path:
            print("Can't find config file: '%s'" % path)
            print("There should be a default '%s' file" % DEFAULT_PATH)
        else:
            print("Cannot default config file '%s'" % path)
    except EnvironmentError as exc:
        print("Couldn't open '%s': %s" % (path, exc))
    else:
        with config_file:
            try:
                data = yaml.load(config_file.read())
                if not isinstance(data, dict):
                    raise yaml.parser.ParserError
                merge(config, DEFAULT_CFG)
                merge(config, data, key_check=True)
                return True
            except yaml.parser.ParserError as exc:
                print("Invalid config file '%s': %s" % (path, exc))
                return
