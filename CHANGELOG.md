## Change Log

All notable changes to this project will be documented in this file.

### [[v0.2.2](https://github.com/Zeroji/semicolon/releases/tag/v0.2.2)]

#### Added

+ MISC (Installs Semicolon Cogs) configuration / installation tool  
  Also works as a launcher, effectively replacing the old `run.sh`
+ Python 3.7 support

### [[v0.2.1](https://github.com/Zeroji/semicolon/releases/tag/v0.2.1)]

#### Added

+ Websocket management for future integration with webserver
+ Sub-cogs now have a `parent` attribute pointing to their parent if any
+ Cog with esoteric languages interpreter, like Brainf\*ck
+ Commands can now return `Embed` objects
+ Event handlers for cogs!

#### Fixed

* `text || ;command` syntax didn't work

#### Changed

* **Switched to discord.py\[rewrite\]**
* **BREAKING** Renamed `server` to `guild` in the configuration file,
  you will need to modify manually if you had changed it
* Configuration files containing string IDs will have to be changed
  to numeric (integer) IDs
* Better convention compliance for Python and Markdown files

#### Removed

- Reaction handling with special cog decorators has been removed to the
  preference of the new event dispatch capabilities.

### [[v0.2.0](https://github.com/Zeroji/semicolon/releases/tag/v0.2.0)]

#### Added

+ Disabling a cog disables its sub-cogs
+ Banned users are actually banned
+ Internationalization mechanisms
+ Server specific language settings
+ Small (bash) script to generate translation templates
+ Fallback commands when permissions aren't met
+ Possibility to hide commands from `help`
+ `prefix set` allows removing old prefixes and adding new ones
+ Added unit tests to `gearbox` and `config`
+ Server specific timezone settings

#### Changed

* `prefix` and `breaker` commands are in the `settings` cog
* `help` now only displays commands you have permission to use
* More helpful "Invalid argument count" message

#### Fixed

* Server configuration not being loaded properly
* Fixed `enable *` and `disable *` output when nothing is changed
* Bot breaking when one cog fails to load
* Proper error message when `cog` isn't defined
* Possible failure on malformed config files

### [[v0.1.4](https://github.com/Zeroji/semicolon/releases/tag/v0.1.4)]

#### Added

+ `info` command with bot / Python / Discord versions
+ Displaying version number in *Playing* status
+ Cog-specific configuration files (yaml or json)
+ Default `config.yaml` file uploaded
+ `breaker` command to change the breaker character per server
+ Argument type in annotations can be a set of strings
+ Included default configuration, checks against type mismatches
+ Added very simple installer

#### Fixed

* Not naming a sub-cog explicitly may crash the bot

#### Removed

- Default configuration file generation with `--generate`

### [[v0.1.3](https://github.com/Zeroji/semicolon/releases/tag/v0.1.3)]

#### Added

+ Extra documentation on all cogs
+ Sub-cogs!
  + Create a folder with an `__init__.py` file in it, that'll be like a normal cog
  + Any cog placed in this folder will become a sub-cog
+ Special documentation pages in `help`
+ Added things to `cipher`:
  + Caesar cipher (finally)
  + Language detection by bigram analysis
  + Automatic Caesar solving (multiple languages)

#### Changed

* `enable` and `disable` work with multiple cogs
* `help` now displays command aliases
* `help` can display special documentation with `-d page`
* Flags can now be called with `-a-b` or `-a -b` (instead of only `-ab` previously)

#### Fixed

* `help` displaying base name of renamed commands

### [[v0.1.2](https://github.com/Zeroji/semicolon/releases/tag/v0.1.2)]

#### Added

+ Per-server prefixes
+ Changelog file ;)
+ Added type checking on command arguments, done with type hints
+ Possibility to to regex checks on arguments
+ Added basic support for argument documentation (you can add it without errors,
  but it's not used yet)
+ Added reaction support via `@cog.on_reaction` (more in doc)
+ `help` command, finally!

#### Changed

* Flags in `@cog.command` can now be either a string or a dictionary
  `{flag: description}` (for future documentation)

#### Fixed

* `Invalid argument count` when passing no arguments to a command using
  positional arguments
* Private message channels are now considered as servers (regarding settings)

### [[v0.1.1](https://github.com/Zeroji/semicolon/releases/tag/v0.1.1)]

#### Added

+ Configuration file
+ Command-line arguments and debug mode
  + `-c file.yaml` to load a configuration file
  + `-l cog` to load a specific cog (can be used multiple times)
  + `--generate file.yaml` to generate a default config file
+ Shutdown and restart mechanism
+ Flags (like `-c`) for commands (see argument changes)
+ Message deletion feature
+ Permission restriction system
+ Per-server settings
+ Ability to enable or disable cogs per server

#### Changed

* Switched from Python 3.5 to 3.6
* Improved logging
* Argument parsing system
  * Commands needing all the message as one argument (like `;say`) must be
    declared with `@cog.command(fulltext=True)`
  * Commands can be passed positional arguments if they are declared like
    `def function(*pos_args)`
  * Command arguments can have default values
  * Commands can be passed bash-like flags

#### Fixed

* Coroutine commands not detected as such

### [[v0.1.0](https://github.com/Zeroji/semicolon/releases/tag/v0.1.0)]

#### Added

+ Commands
  + Basic argument parsing
+ Cog system
  + Possibility to rename or alias commands
  + On init and on exit functions
+ Callable commands
+ `|` mechanism to chain commands
+ Wheel system
  + Dynamic loading of new cogs
  + Dynamic reloading of modified cogs
