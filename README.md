## ;;

> v0.1.1

This is the repository for the *new* version of `;;`,
a nice Discord bot with currently very few features.  
[Old version here.](http://github.com/Zeroji/semicold)

If you want to add features, feel free to [write a cog](https://github.com/Zeroji/semicolon/blob/master/docs/cogs.md)!

> *A side note about the `data` folder which is ignored*  
`data/secret/token` contains the bot's token  
`data/admins` and `data/banned` contain newline-separated IDs  
`data/master` contains the owner's ID  

#### How to use

Clone this repo, run `pip install -r requirements`, then`./core.py`  
Since v0.1.1 you'll need Python 3.6 - currently, 3.6.0b3 is available.

#### How to use (Discord side)

When the bot status gets yellow (idle), it means everything is properly loaded.  
You can then call commands by typing `;command whatever arguments it takes`.
If two cogs have the same command, type `;cog.command` to differentiate them.

#### Fancy new stuff in last version

`;;` can now interpret commands inside other messages, if you use a "breaker" character.
This character defaults to `|` and can be set in `core.py`.  
A quick how-to:  
`Hello, can you say |;hi| ?` is equivalent to `;hi`  
`Hello, can you ||;say hi | test` is equivalent to `;say hi | test`  
Basically, this splits your messages in chunks delimited by `|` and evaluates them separately.
If `;;` encounters `||`, it stops splitting and sends all the remaining text as one chunk: useful
when said text contains a `|` 