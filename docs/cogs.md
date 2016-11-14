## How to write your cog

`;;` draws its main features from modules, named "cogs".  
Writing one is rather straightforward, but a couple rules have to be respected.

### Match `[a-z][a-z_0-9]*\.py`

Don't run away ~~yet~~! This simply means that the name of your file must be **full lowercase** and it has to start by a letter (any file starting with `_` or a digit will be ignored). Once you have that file, just drop it in the `cogs` folder and that's all.

> Also, don't erase `base.py` - you can rename it if needed, but it's quite essential.

### Don't forget your tools

Every cog must contain a `cog` variable, which has to be an instance of `gearbox.Cog`. Here's what a standard cog header looks like:  
```python
import gearbox
cog = gearbox.Cog()
```
> By default, your cog's name will be the file name, minus the `.py` part.  
To change this, simply pass a new name as an argument to `gearbox.Cog()`.

### Creating a command

#### The basics

If you're familiar with `discord.py`, then you probably know about `async`, `await` and all that stuff. If not, don't worry! You don't need that to write stuff.

Every command must be "decorated" by placing `@cog.command` before its definition. After that step, it'll be recognized by `;;` as a command - as long as it has a valid name (see above). Here's a really simple command:

```python
@cog.command
def hello():
    return 'Hello, world!'
```

Straightforward, right? Your command just has to return something, and `;;` will send it in the good channel. If you return nothing... Well, nothing happens.  
But what if you want it to greet someone specifically?

#### Special arguments

Greeting a user can be done very simply:

```python
@cog.command
def hello(author):
    return f'Hello, {author.name}!' 
```

> If you really aren't familiar with `discord.py`, have a look at [their documentation](http://discordpy.readthedocs.io/en/latest/). For very simple usage, you can get a user/channel/server name with `.name`.

> Wondering what this `f'{}'` thing does? Basically, it's the same as `'Hello, ' + author.name + '!'` but shorter and fancier.
[Learn more here](https://www.python.org/dev/peps/pep-0498/)

As you can see, simply putting `author` in the function definition will give you the corresponding object. Why? Because `;;` is made in such a way that it'll look at what you want, and attempt to provide it to you so you don't need to write extra pieces of code. Here's a list of those "special" arguments: *(as of v0.1.1)*

|Argument    | Description
|-
|`client`    | The application's `discord.Client()`
|`message`   | The Message object which was sent - don't use like a string!
|`author`    | Shortcut for `message.author`
|`channel`   | Shortcut for `message.channel`
|`server`    | Shortcut for `message.server`
|`server_ex` | Special bot object including things like server config
|`flags`     | Flags specified by the user, if your command uses flags

*Remember that using those will give you special values, which might not correspond to your expectations.*

> **Side note about flags**  
Flags with `;;` are like flags in Bash: if the first argument of your command
starts with a dash (`-`), the letters behind if, called "flags", will be sent to the command.
You can specify which flags your command accept. Flags are case-sensitive. Quick example:
> ```python
> @cog.command(flags='abc')
> def flag(flags):
>     return f'I got {flags}'
> ```
> Now if you call `;flag -ab`, it'll reply `I got ab`.


#### Normal arguments

Now maybe you simply want to write a `repeat` command, but you don't know how to get the text? Just ask for it!

```python
@cog.command
def repeat(what_they_said):
    return what_they_said
```

Now, this may lead to an `Invalid argument count` error. That's because since v0.1.1,
`;;` has to be told explicitly when you want all the remaining text to be sent to your function:

```python
@cog.command(fulltext=True)  # Adding this bit allows the command to work nicely
def repeat(what_they_said):
    return what_they_said
```

When sending arguments to commands, `;;` will take care of special arguments, then send the rest of the message to the other arguments. If you need multiple arguments, just define them!

```python
@cog.command
def add(number_a, number_b):
    return str(int(number_a) + int(number_b))
```

> *May change in future versions (last changed v0.1.1)*  
If the user doesn't provide the arguments you need, for example if they type `add 4`, `;;` will print `Invalid argument count` in the chat, and your command won't be executed.
If the user sends too many arguments, for example by typing `add 1 2 3`, the same thing will happen.

Now what if you'd like to have default argument? Let's say you want `add` to add 1 if `number_b` isn't specified:
with the new version, just do like you'd do with regular Python functions!

```python
@cog.command
def add(number_a, number_b=1):  # If number_b isn't specified, it'll be 1
    return str(int(number_a) + int(number_b))
```

#### More arguments!

Let's say you want to have a command that takes a string, then a series of strings, and inserts that first string between all the others, i.e. `, 1 2 3` would give `1,2,3` - wow, that's just like `str.join()`!  
You'll want to have the first argument, then "all the rest". Of course, you could be using `def join(my_string, all_the_rest):` along with `fulltext=True` and then use `.split()`, but ;; can do that for you! Simply add `*` before your last argument, and it'll receive a nice little list of whatever was sent:

```python
@cog.command
def join(my_string, *all_the_rest):
    return my_string.join(all_the_rest)
```

#### About `async` and `await`

What if you're an advanced user and you know all that async stuff already and just want to add your tasks to the event loop while awaiting coroutines?

```python
async def command(client):
```

It's that simple. If your command is a coroutine, then `;;` will simply `await` it (if you want to send a message, do it yourself!); and the `client` argument will give you access to the main client. Hint, the loop is at `client.loop`

### Decorating your command

No, this isn't about adding a cute little ribbon onto it. *(as of v0.1.1)*.
Also, this technically adds functionalities to the cog rather than to the command.

You've already used the decorator `@cog.command` to indicate that your function was a `;;` command and not a random function.  
You can do a bit more, here, have a list:

##### `@cog.rename(name)`
This will change the name of your command. It's useful, for example, if you want your command to be called `str` but you can't because of Python's `str()` function. Just call your function `asdf` and put `@cog.rename('str')` before it.

##### `@cog.alias(alias, ...)`
This creates aliases for your command. Let's say you find `encrypt` is a quite long name, just add `@cog.alias('en')` and you'll be able to call your command with `encrypt` *and* `en`.

##### `@cog.init`
This doesn't apply to a command, but to a regular function - it marks it, so it will be called when the cog is loaded. You can only have one init function.

##### `@cog.exit`
This doesn't apply to a command, but to a regular function - it marks it, so it will be called when the cog is unloaded. You can only have one exit function.

### Getting the best out of `@cog.command`

If you've read all the above doc, you saw `@cog.command(fulltext=True)`:
indeed, the `@cog.command` decorator can take a couple special parameters, here's the list

##### `fulltext` (boolean, defaults to `False`)

This argument, when set to `True`, will allow your command to receive all the text the user wrote, for example:
```python
@cog.command(fulltext=True)
def say(text):
    return text
```

If you call `;say Hello world!` it'll repeat it, but if `fulltext` was set to `False` it would have resulted in an `Invalid argument count` error.

`delete_message` (boolean, defaults to `False`)

If this option is enabled, `;;` will try to delete the user's message after the command was executed.

`permissions` (string, tuple or list, defaults to `None`)

This one is a bit trickier: it allows you to specify that a user needs certain permissions for running a command.
Say you want only users with `manage_server` permission to use your command, you could use one of the following:
```python
@cog.command(permissions='manage_server')
@cog.command(permissions=('manage_server', True))
@cog.command(permissions=['manage_server'])
@cog.command(permissions=[('manage_server', True)])
```

The more complex forms are useful, because you can set complicated behaviour: what if you want your command to be
available only to non-admins who can delete messages?

```python
@cog.command(permissions=[('manage_server', False), 'manage_messages'])
```

> As of v0.1.1, no error message is printed in case of wrong permissions.  
This is intended behaviour.

`flags` (string, defaults to `''`)

This allows you to tell `;;` which flags can be used by the command.
An error message will be printed if the user tries to use an invalid flag.
See the [Special arguments](#special-arguments) section above for more information about flags.

### Using your cog

As written above, you just need to drop it in the `cogs` folder!  
> Side note: make sure you have the `import gearbox; cog = gearbox.Cog('name')` part, otherwise `;;` will consider the file broken and won't load it until it restarts.

If `;;` is running, it'll automatically load it within a couple of seconds, and reload it when you edit it. Don't worry, if you break stuff, it'll keep running the old code until the new one is working.  
If you have name conflicts with another module, call your commands with `cog_name.command_name` to avoid collisions.
