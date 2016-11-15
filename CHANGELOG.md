## Change Log
All notable changes to this project will be documented in this file.

### [Unreleased]

#### Added

+ Per-server prefixes
+ Changelog file ;)

#### Changed

#### Fixed

* `Invalid argument count` when passing no arguments to a command using positional arguments
* Private message channels are now considered as servers (regarding settings)

### [v0.1.1]

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

### [v0.1.0]

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
