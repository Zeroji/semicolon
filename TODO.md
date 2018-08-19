# Planned features and future possibilities

This file contains a list of features and things which may or may not be
present in future versions. Stuff under the [Soon](#soon) category will be
done at some point in the future, items in other sections might be discarded
or heavily modified.

## Soon

This is currently empty because I haven't decided what to work on.

## Project management

- Clean-up TODO list
- Possible reStructuredText documentation
- `.editorconfig` file

## Implementation

### Main features

#### Installation [misc.py]

- Auto-detection of cog requirements
- Cog loading list in configuration file

#### Guild management

- Grant / restrict access to commands to certain users / roles
- Change default permissions of commands
- Blacklist / whitelist commands
- Blacklist / whitelist commands in channels
- Blacklist / whitelist users / roles

### Command API

- DM-only commands
- Hide commands from `;help`

#### Arguments

- `is_private` to determine if it's a DM
- `rank` if ever implemented server-side

#### Permissions

- Bot owner (from configuration file)
- Bot admins (from configuration file)
- Bot users (generally disallowed)
- Server-side bot admins (custom role)

### Cog API

- Cog-wide permissions (hides cog if disallowed)
- Cron-like scheduled tasks
- Websocket-triggered functions
  - Possibility of a webserver to receive webhooks
- Annotation for `pip` requirements
- Possibility to hide cog from guilds except whitelist
- Possibility to be disabled by default
- Per guild / channel / user configuration files (file descriptors)

### Miscellaneous

- Guild configuration file at `guilds/<guild>.json`
  - Cogs data at `guilds/<guild>/<cog>.json`
- [List of time zones][tzlist] for custom server TZ

[tzlist]: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

## Deployment

- Clean up stray files from older versions
