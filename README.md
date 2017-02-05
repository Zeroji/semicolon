## ;;

> v0.2.0

This is the repository for the *new* version of `;;`,
a nice Discord bot with currently very few features.  
[Old version here.](http://github.com/Zeroji/semicold)

If you want to add features, feel free to [write a cog](https://github.com/Zeroji/semicolon/blob/master/doc/cogs.md)!

#### How to use

Clone this repo, then run `pip install -r requirements`  
Edit `config.yaml` if you need to, or create another config file
  
> The paths `token`, `master`, `admins` and `banned` must exist  
> Alternatively, you can run `./install.py` for a minimalistic setup

To run the bot, type `./core.py` or `./core.py -c your_config.yaml`  
Since [v0.1.1](https://github.com/Zeroji/semicolon/releases/tag/v0.1.1) you'll need Python 3.6.

#### How to use (Discord side)

When the bot status gets yellow (idle), it means everything is properly loaded.  
You can then call commands by typing `;command whatever arguments it takes`.
If two cogs have the same command, type `;cog.command` to differentiate them.  
Since multiple bots may use the `;` prefix, you can also mention `;;` instead of using the prefix:
`@;; cog.command arguments`. You can also change the prefix to your liking if you have
the `Manage Server` permission, check `@;; help prefix`.

#### Fancy ways to use commands

`;;` can now interpret commands inside other messages, if you use a "breaker" character.
This character defaults to `|` and can be changed with the `breaker` command.  
A quick how-to:  
`Hello, can you say |;hi| ?` is equivalent to `;hi`  
`Hello, can you ||;say hi | test` is equivalent to `;say hi | test`  
Basically, this splits your messages in chunks delimited by `|` and evaluates them separately.
If `;;` encounters `||`, it stops splitting and sends all the remaining text as one chunk: useful
when said text contains a `|` 