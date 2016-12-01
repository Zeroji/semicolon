## Change Log
All notable changes to this project will be documented in this file.

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
+ Added basic support for argument documentation (you can add it without errors, but it's not used yet)
+ Added reaction support via `@cog.on_reaction` (more in doc)
+ `help` command, finally!

#### Changed

* Flags in `@cog.command` can now be either a string or a dictionary `{flag: description}` (for future documentation)

#### Fixed

* `Invalid argument count` when passing no arguments to a command using positional arguments
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
  * Commands needing all the message as one argument (like `;say`) must be declared with `@cog.command(fulltext=True)`
  * Commands can be passed positional arguments if they are declared like `def function(*pos_args)`
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
