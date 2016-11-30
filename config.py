"""Handle ;;'s config."""
import collections
import yaml.parser


DEFAULT_PATH = 'config.yaml'


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
                merge(config, data)
                return True
            except yaml.parser.ParserError as exc:
                print("Invalid config file '%s': %s" % (path, exc))
                return
