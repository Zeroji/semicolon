"""Handle ;;'s config."""
import collections
import yaml

DEFAULT_PATH = 'config.yaml'
DEFAULT_CONFIG = """
path:
    log:    run.log
    token:  data/secret/token
    master: data/master
    admins: data/admins
    banned: data/banned
wheel:
    import: true
    reload: true
""".lstrip()


def merge(dest, update):
    """Recursively update a nested dictionnary."""
    # [From StackOverflow](http://stackoverflow.com/a/3233356)
    for key, value in update.items():
        if isinstance(value, collections.Mapping):
            temp = merge(dest.get(key, {}), value)
            dest[key] = temp
        else:
            dest[key] = update[key]
    return dest


def load(given_path, config):
    """Load config from file or default."""
    config.update(yaml.load(DEFAULT_CONFIG))
    path = given_path or DEFAULT_PATH

    try:
        config_file = open(path, mode='r')
    except FileNotFoundError:
        if given_path:
            print("Can't find config file: '%s'" % path)
            print("Use --generate <path> to create one")
        else:
            if write(DEFAULT_PATH):
                print("Created default config file '%s'" % path)
    except EnvironmentError as exc:
        print("Couldn't open '%s': %s" % (path, exc))
    else:
        with config_file:
            try:
                data = yaml.load(config_file.read())
                if not isinstance(data, dict):
                    raise yaml.scanner.ScannerError
                merge(config, data)
            except yaml.scanner.ScannerError as exc:
                print("Invalid config file '%s': %s" % (path, exc))
                return


def write(path):
    """Write default config to a file."""
    try:
        config_file = open(path, 'w')
    except EnvironmentError as exc:
        print("Couldn't create config file '%s': %s" % (path, exc))
    else:
        config_file.write(DEFAULT_CONFIG)
        config_file.close()
        return True
