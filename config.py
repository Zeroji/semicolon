"""Handle ;;'s config."""
import collections
import unittest
import yaml.parser


# If no path is specified, this path is used
DEFAULT_PATH = 'config.yaml'
# If config options are missing, those are used
DEFAULT_CFG = {
    'path': {
        'log': 'run.log',
        'token': 'data/secret/token',
        'master': 'data/master',
        'admins': 'data/admins',
        'banned': 'data/banned',
        'guild': 'data/guilds/%s.json',
        'config': 'config/%s.%s',
        'version': 'version',
        'locale': 'locale',
    }, 'wheel': {
        'import': True,
        'reload': True,
    }, 'port': {
        'websocket': 8765
    }
}


class TestConfig(unittest.TestCase):
    def assertSameKeys(self, d1, d2, msg=None):
        self.assertIsInstance(d1, dict, msg)
        self.assertIsInstance(d2, dict, msg)
        for key, value in d1.items():
            self.assertIn(key, d2, msg)
            if isinstance(value, dict):
                self.assertIsInstance(d2[key], dict, msg)
                self.assertSameKeys(value, d2[key])
            else:
                self.assertNotIsInstance(d2[key], dict, msg)
        for key in d2:
            self.assertIn(key, d1)

    def test_same_keys(self):
        self.assertSameKeys({}, {})
        self.assertSameKeys({'a': 1}, {'a': 2})

        self.assertRaises(AssertionError, self.assertSameKeys, {'a': 1}, {'b': 2})
        # Basic tests
        self.assertSameKeys({}, {})
        self.assertSameKeys({'a': 1}, {'a': 2})
        self.assertSameKeys({'a': 1, 'b': 2}, {'a': 'b', 'b': 'a'})
        # A not in B / B not in A tests
        self.assertRaises(AssertionError, self.assertSameKeys, {'a': 1}, {})
        self.assertRaises(AssertionError, self.assertSameKeys, {}, {'a': 1})
        # Nested tests
        self.assertSameKeys({'d': {'a': 1}}, {'d': {'a': 2}})
        self.assertRaises(AssertionError, self.assertSameKeys, {'d': {'a': 1}}, {'d': {'b': 1}})

    def test_config(self):
        with open(DEFAULT_PATH) as handle:
            data = yaml.load(handle)
            self.assertSameKeys(data, DEFAULT_CFG)

    def test_merge(self):
        self.assertEqual(merge({'a': 1}, {'a': 2}), {'a': 2})
        self.assertEqual(merge({'a': 1}, {'b': 2}), {'a': 1, 'b': 2})
        self.assertEqual(merge({'a': 1}, {'b': 2}, key_check=True, silent=True), {'a': 1})

        self.assertEqual(merge({'a': False}, {'a': 1}), {'a': 1})
        self.assertRaises(ValueError, merge, {'a': False}, {'a': 1}, key_check=True)

        self.assertEqual(merge({'a': {'b': 1, 'c': 3}}, {'a': {'b': 2}}), {'a': {'b': 2, 'c': 3}})
        self.assertEqual(merge({'a': 1, 'b': 2}, {'a': {'c': 3}}), {'a': {'c': 3}, 'b': 2})
        self.assertRaises(ValueError, merge, {'a': 1, 'b': 2}, {'a': {'c': 3}}, key_check=True)


def merge(dest, update, *, key_check=False, silent=False):
    """Recursively update a nested dictionary."""
    # [From StackOverflow](http://stackoverflow.com/a/3233356)
    # Modified to raise ValueError in case of type mismatch, and ignore new keys
    for key, value in update.items():
        if key_check:
            if key not in dest:
                if not silent:
                    print(f"Useless key '{key}' with value '{value}'")
                continue
            if not isinstance(value, type(dest[key])):
                raise ValueError(f"Type mismatch on key '{key}'")
        if isinstance(value, collections.Mapping):
            temp = dest.get(key, {})
            if not isinstance(temp, dict):
                temp = {}
            merge(temp, value, key_check=key_check)  # Recursively merge internal dictionary
            dest[key] = temp
        else:
            dest[key] = update[key]  # Regular key update
    return dest


def load(given_path, config):
    """Populate config from default settings or configuration file."""
    path = given_path or DEFAULT_PATH
    try:
        config_file = open(path, mode='r')
    except FileNotFoundError:
        if given_path:
            print("Can't find config file: '%s'" % path)
            print("There should be a default '%s' file" % DEFAULT_PATH)
        else:  # Missing default config file, shouldn't happen
            print("Cannot default config file '%s'" % path)
        raise
    except EnvironmentError as exc:
        print("Couldn't open '%s': %s" % (path, exc))
        raise
    try:
        data = yaml.load(config_file.read())
        if not isinstance(data, dict):
            raise ValueError('Not a valid dictionary')
        # Update given configuration with defaults
        merge(config, DEFAULT_CFG)
        # Overwrite defaults with parsed data
        merge(config, data, key_check=True)
    except (yaml.parser.ParserError, ValueError) as exc:
        print("Invalid config file '%s': %s" % (path, exc))
        raise
