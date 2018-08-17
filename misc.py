#!/usr/bin/env python
"""misc installs semicolon cogs"""
import argparse
import logging
import os
import re

# Set up logging
logging.basicConfig(format='%(name)s:%(levelname)s:%(message)s')
log = logging.getLogger('misc')
log.setLevel(logging.INFO)

# Check pip installation
try:
    import pip
except (ImportError, ModuleNotFoundError):
    log.critical('pip cannot be found - misc will now exit')
    log.critical('see https://pypi.org/project/pip/ for instructions')
    exit(1)

# Check if PyYAML can be used
try:
    import yaml
except (ImportError, ModuleNotFoundError):
    log.error('PyYAML not installed yet, will use default configuration')
    yaml = False


# Default configuration (just enough)
DEFAULT_CONFIG = {'path': {
    'token': 'data/secret/token',
    'master': 'data/master',
    'admins': 'data/admins'
}}


def check(args, cfg):
    """Verify semicolon installation."""
    if args.token:
        check_token(cfg['path']['token'])


def check_token(path):
    """Verify validity of token."""
    if not os.path.isfile(path):
        log.error('Cannot find token file at %s', path)
        return
    with open(path, 'r') as file:
        token = file.read().strip()
    import urllib.request
    import json
    req = urllib.request.Request('https://discordapp.com/api/users/@me')
    req.add_header('Authorization', 'Bot %s' % token)
    req.add_header('User-Agent', 'MISC installer - github.com/Zeroji/semicolon')
    try:
        response = urllib.request.urlopen(req)
        data = json.load(response)
        log.info('Token verified: %(username)s#%(discriminator)s (ID %(id)s)', data)
    except urllib.error.HTTPError as exc:
        log.warning('HTTP Error %d happened during token verification:', exc.code)
        log.warning(exc.msg)
    except json.JSONDecodeError:
        log.warning('Error during decoding of JSON response')


def run(args, config):
    """Run semicolon"""
    if args.args and args.args[0] == '--':
        args.args = args.args[1:]
    log.info('Running semicolon core' + (' once' if args.once else ''))

    import subprocess
    import time
    delay = 2

    command = ['python', 'core.py']
    command.extend(args.args)

    while True:
        launch = time.time()
        proc = subprocess.Popen(command)
        code = proc.wait()
        elapsed = time.time() - launch
        log.debug('Stopped after %d seconds', elapsed)

        # Handle exit codes
        if code == 69:
            log.info('Received exit code, stopping')
            break
        elif code == 82:
            if not args.once:
                log.info('Received restart code, restarting')
                continue
        else:
            log.warning('Unplanned shutdown with exit code %d', code)

        if args.once:
            log.debug('Stopping due to --once flag')
            break

        # Wait a bit before restarting in case we're spamming the API
        # If the bot didn't last 5 minutes, progressively increase wait time
        if elapsed > 300:
            delay = 2
        elif delay < 120:
            delay *= 2
        log.debug('Restarting semicolon in %d seconds', delay)
        time.sleep(delay)

COMMANDS = {'check': check, 'run': run}


def main():
    if not os.path.isfile('core.py') or not os.path.isdir('cogs'):
        log.critical('Cannot find semicolon, make sure this is the right folder')
        return

    # Main argument parser
    parser = argparse.ArgumentParser(description='MISC tool to help setup semicolon')
    parser.add_argument('-v', '--verbose', action='store_const', const=True,
                        default=False, help='Display debug-level information')
    parser.add_argument('-q', '--quiet', action='store_const', const=True,
                        default=False, help='Only display errors')
    parser.add_argument('-c', '--config', action='store', metavar='file',
                        default='config.yaml', help='specify the config file')
    sub = parser.add_subparsers(dest='command')

    # Subcommand argument parsers
    parser_check = sub.add_parser('check', help='Check semicolon installation')
    parser_check.add_argument('-t', '--token', action='store_const', const=True,
                              default=False, help='Check token validity')

    parser_run = sub.add_parser('run', help='Run semicolon')
    parser_run.add_argument('--once', action='store_const', const=True,
                            default=False, help='Run only once (disable restart)')
    parser_run.add_argument('args', nargs=argparse.REMAINDER, help='Semicolon args')

    args = parser.parse_args()
    if args.command is None:
        log.error('Expected a command, use --help for more information')
        return

    if args.verbose:
        log.setLevel(logging.DEBUG)
    if args.quiet:
        log.setLevel(logging.ERROR)

    # Read config from file if available
    config = DEFAULT_CONFIG
    if yaml:
        if not os.path.isfile(args.config):
            log.warning('Cannot find configuration file, will use default configuration')
        else:
            with open(args.config, 'r') as file:
                config = yaml.load(file)

    COMMANDS[args.command](args, config)

if __name__ == '__main__':
    main()
