## How to write your cog

`;;` draws its main features from modules, named "cogs".  
Writing one is rather straightforward, but a couple rules have to be respected.

### Match `[a-z][a-z_0-9]*\.py`

Don't run away ~~yet~~! This simply means that the name of your file must be
**full lowercase** and it has to start by a letter (any file starting with `_`
or a digit will be ignored). Once you have that file, just drop it in the
`cogs` folder and that's all.

> Also, don't erase `base.py` - you can rename it if needed, but it's quite essential.

### Don't forget your tools

Every cog must contain a `cog` variable, which has to be an instance of
`gearbox.Cog`. Here's what a standard cog header looks like:

```python
import gearbox
cog = gearbox.Cog()
```

By default, your cog's name will be the file name, minus the `.py` part.  
To change this, simply pass a new name as an argument to `gearbox.Cog()`.

```python
import gearbox
cog = gearbox.Cog('my_awesome_cog')
```

> Since [v0.1.4], you can have a specific config file just for your cog,
> just add a `config` argument with the value `json` or `yaml`:
> ```python
> import gearbox
> cog = gearbox.Cog('my_awesome_cog', config='yaml')
> print(cog.config)
> ```
> If the file exists, `cog.load_cfg()` is automatically created. After you write
> changes to the `cog.config` dictionary, you can use `cog.save_cfg()`.

### Cogception

If you're an organized person, you might dislike the "drop it in the folder" part.
That's why `;;` has sub-cogs! Start by creating a cog that can accept sub-cogs:

- Make a new folder with the name of your cog
- Inside it, create an `__init__.py` file - this will be your source code,
  use it like a regular cog source file

Now you can drop other cogs in that folder, and they'll be all neatly organized!
Note that disabling a cog also disables its sub-cogs.

> Yes, you can have sub-sub-cogs. And so on.

### Creating a command

#### The basics

If you're familiar with `discord.py`, then you probably know about `async`, `await`
and all that stuff. If not, don't worry! You don't need that to write stuff.

Every command must be "decorated" by placing `@cog.command` before its definition.
After that step, it'll be recognized by `;;` as a command - as long as it has a
valid name (see above). Here's a really simple command:

```python
@cog.command
def hello():
    return 'Hello, world!'
```

Straightforward, right? Your command just has to return something, and `;;` will
send it in the good channel. If you return nothing... Well, nothing happens.  
But what if you want it to greet someone specifically?

#### Special arguments

Greeting a user can be done very simply:

```python
@cog.command
def hello(author):
    return f'Hello, {author.name}!'
```

> If you really aren't familiar with `discord.py`, have a look at
> [their documentation](http://discordpy.readthedocs.io/en/latest/). For very
> simple usage, you can get a user/channel/server name with `.name`.

> Wondering what this `f'{}'` thing does? Basically, it's the same as
> `'Hello, ' + author.name + '!'` but shorter and fancier.
> [Learn more here](https://www.python.org/dev/peps/pep-0498/)

As you can see, simply putting `author` in the function definition will give you
the corresponding object. Why? Because `;;` is made in such a way that it'll
look at what you want, and attempt to provide it to you so you don't need to
write extra pieces of code. Here's a list of those "special" arguments:
*(as of [v0.2.0])*

|Argument    | Description
| ---        | ---
|`client`    | The application's `discord.Client()`
|`message`   | The Message object which was sent - don't use like a string!
|`author`    | Shortcut for `message.author`
|`channel`   | Shortcut for `message.channel`
|`server`    | Shortcut for `message.server`
|`server_ex` | Special bot object including things like server config
|`flags`     | Flags specified by the user, if your command uses flags

*Remember that using those will give you special values,
which might not meet your expectations.*

> **Side note about flags**  
> Flags with `;;` are like flags in Bash: if the first argument of your command
> starts with a dash (`-`), the letters behind it, called "flags", will be sent
> to the command. You can specify which flags your command accept. Flags are
> case-sensitive. Quick example:
>
> ```python
> @cog.command(flags='abc')
> def flag(flags):
>     return f'I got {flags}'
> ```
>
> Now if you call `;flag -ab`, it'll reply `I got ab`.  
> Since [v0.1.3], writing `;flag -a-b` or `;flag -a -b` is also accepted.

#### Normal arguments

Now maybe you simply want to write a `repeat` command, but you don't know how
to get the text? Just ask for it!

```python
@cog.command
def repeat(what_they_said):
    return what_they_said
```

Now, this may lead to an `Invalid argument count` error. That's because since
[v0.1.1], `;;` has to be told explicitly when you want all the remaining text
to be sent to your function:

```python
@cog.command(fulltext=True)  # Adding this bit allows the command to work nicely
def repeat(what_they_said):
    return what_they_said
```

When sending arguments to commands, `;;` will take care of special arguments,
then send the rest of the message to the other arguments. If you need multiple
arguments, just define them!

```python
@cog.command
def add(number_a, number_b):
    return str(int(number_a) + int(number_b))
```

> *May change in future versions (last changed [v0.1.1])*  
If the user doesn't provide the arguments you need, for example if they type
`add 4`, `;;` will print an error message in the chat, and your command won't
be executed. If the user sends too many arguments, for example by typing
`add 1 2 3`, the same thing will happen.

Now what if you'd like to have default arguments? Let's say you want `add` to
add 1 if `number_b` isn't specified: since [v0.1.1], just do like you'd do with
regular Python functions!

```python
@cog.command
def add(number_a, number_b=1):  # If number_b isn't specified, it'll be 1
    return str(int(number_a) + int(number_b))
```

#### More arguments!

Let's say you want to have a command that takes a string, then a series of
strings, and inserts that first string between all the others, i.e. `, 1 2 3`
would give `1,2,3` - wow, that's just like `str.join()`!  
You'll want to have the first argument, then "all the rest". Of course, you
could be using `def join(my_string, all_the_rest):` along with `fulltext=True`
and then use `.split()`, but ;; can do that for you! Simply add `*` before your
last argument, and it'll receive a nice little list of whatever was sent:

```python
@cog.command
def join(my_string, *all_the_rest):
    return my_string.join(all_the_rest)
```

#### About `async` and `await`

What if you're an advanced user and you know all that async stuff already and
just want to add your tasks to the event loop while awaiting coroutines?

```python
async def command(client):
```

It's that simple. If your command is a coroutine, then `;;` will simply `await`
it (if you want to send a message, do it yourself!); and the `client` argument
will give you access to the main client. Hint, the loop is at `client.loop`

### Documenting your command

> a.k.a. adding a cute little ribbon on it

You may have seen this wonderful `help` command in the `base` cog, which does
some really neat stuff, like displaying what a command does, which arguments
to use and all. Sadly, this information isn't magically generated: you have
to add it to your command or it won't work.

#### What your command does

This is done by adding a triple-quote string (`"""like this"""`) at the
very beginning of your command:

```python
@cog.command
def documentation():
    """Print documentation about how to document.

    This is an additional **text message**, feel free to use some __fancy__ Discord formatting!
    Newlines are respected, *don't worry*! You can even put some `code blocks`."""
```

When calling `help <your_cog>`, only the first line will be displayed (on the right
side), but with `help <your_command>` it'll display the first line, then arguments
and related stuff, and finally your additional documentation.  
It is recommended you avoid using Discord formatting in the first line.

#### Flags documentation

You may have seen flags earlier, they are some kind of one-letter arguments that are
either present or absent:

```python
@cog.command(flags='abc')
def show_flags(flags):
    return f'I got the following flags: {flags}'
```

Here, the only information `;;` has about this command is that it can take the flags
`a`, `b` and `c`. But what do these do? Well, let's use a dictionary to define that!

```python
@cog.command(flags={
    'a': "Wow that's an A!",
    'b': 'Execute plan B',
    'c': ''
})
```

With a dictionary, you can write `key:value` couples, with the `key` being your flag
and the `value` a short description of its use. If you don't want to specify a value
for a certain flag, set it to `''` (empty string).

#### Arguments documentation

##### Annotations

First of all, any "special" argument to your command will *not* be displayed:
that's normal, because those are supposed to be internal arguments.  
Normal arguments can have two values added to them: a *type*, for example
your `add(x, y)` function generally takes `int` objects; and a *documentation
string* which `help` uses to display even more information.  
Now, both those values are optional, and you can write one without the other,
but here how it's done:

```python
@cog.command
def add(a: int, b: int)
def add(a: 'An integer', b: 'Another integer')
def add(a: (int, 'An integer'), b: ('Another integer', int))
```

As you can see, the syntax is quite modular: you can write either one, or the other,
or both - in any order. Note that the *preferred* syntax is `(type, 'docstring')`.  
If you want to have a default value, add it *after* the annotation:

```python
@cog.command
def add(a: int, b: int=4)
def add(a: 'An integer'=2, c: ('This one is a float', float)=3.14)
```

##### Type annotations

Now, here's something cool about that `type` thingy: it automatically
converts stuff! In the previous example, if the user were to type `add 2 6`,
your command wouldn't receive the strings `'2'` and `'6'` but the *integers*
`2` and `6`! Note that this only works with types that allow casting from a
string. For convenience, it's implemented for `bool`: any variation of "true",
"yes" or "1" will be cast to `True` while "false", "no" or "0" will give `False`.  
If the argument cannot be cast, an error is displayed.

But wait, there's more! If you love regular expression, you can put a regex
pattern instead of a type, for example to input an email:

```python
@cog.command
def send(address: re.compile(r'^[\w.-]*@[\w-]*\.[\w]*$')):
```

This might look tricky, if you're not used to regular expressions you should
either discard this information (hint: don't) or learn about them (hint: do).  
If the argument doesn't match the pattern, an error is displayed.

A last thing you can do: instead of a type, or regexp pattern, you can specify
a `set` of strings: an example is the command `prefix` which takes `get`, `add`,
`del` or `reset` as its first argument:

```python
@cog.command
def prefix(command: {'get', 'add', 'del', 'reset'}='get'):
```

This specifies that this argument can only have those values (the check is
case-insensitive, but if the argument's case will be converted to match yours),
and defaults to `get` if no value is set by the user. If the value isn't in the
string set, an error is displayed.

> Note: the {element1, element2, element3} construction is a *set*, like a list
> except an element cannot be present twice. It's very important that you use
> a set, and not a list or tuple, otherwise your command just won't work.

### Decorating your command

*Technically, this adds features to the cog rather than to the command.*

You've already used the decorator `@cog.command` to indicate that your function
was a `;;` command and not a random function.  
You can do a bit more, here, have a list:

#### `@cog.rename(name)`

This will change the name of your command. It's useful, for example, if you want
your command to be called `str` but you can't because of Python's `str()`
function. Just call your function `asdf` and put `@cog.rename('str')` before it.

#### `@cog.alias(alias, ...)`

This creates aliases for your command. Let's say you find `encrypt` is a quite
long name, just add `@cog.alias('en')` and you'll be able to call your command
with `encrypt` *and* `en`.

#### `cog.hide`

This will simply hide your command. This means that anything which, like `help`,
gives a list of commands, won't show this one. Very useful for hiding your fallback
commands (see below).

### Getting the best out of `@cog.command`

If you've read all the above doc, you saw `@cog.command(fulltext=True)`: indeed,
the `@cog.command` decorator can take a couple special parameters, here's the list

#### `fulltext` (boolean, defaults to `False`)

This argument, when set to `True`, will allow your command to receive all the
text the user wrote, for example:

```python
@cog.command(fulltext=True)
def say(text):
    return text
```

If you call `;say Hello world!` it'll repeat it, but if `fulltext` was set to
`False` it would have resulted in an `Invalid argument count` error.

#### `delete_message` (boolean, defaults to `False`)

If this option is enabled, `;;` will try to delete the user's message after the
command was executed.

#### `permissions` (string, tuple or list, defaults to `None`)

This one is a bit trickier: it allows you to specify that a user needs certain
permissions for running a command. Say you want only users with `manage_server`
permission to use your command, you could use one of the following:

```python
@cog.command(permissions='manage_server')
@cog.command(permissions=('manage_server', True))
@cog.command(permissions=['manage_server'])
@cog.command(permissions=[('manage_server', True)])
```

The more complex forms are useful, because you can set complicated behaviour: what
if you want your command to be available only to non-admins who can delete messages?

```python
@cog.command(permissions=[('manage_server', False), 'manage_messages'])
```

#### `fallback` (string) (optional)

> Please read the paragraph above about the `permissions` argument if you haven't already.

The `fallback` argument is used to call another command when permissions aren't met:
for example, the `settings.lang` command requires the "manage_server" permission, but
it has a fallback command which only displays languages when someone tries to use it
with insufficient permissions.

```python
@cog.command(permissions='manage_messages', fallback='delete2')
def delete(channel, number=1):
    """This is the main command"""
    # ...

@cog.command
def delete2(number=1):
    """This is the fallback"""
    return "Insufficient permissions to delete messages"
```

> You can use `@cog.hide` to prevent `delete2` from being listed.

#### `flags` (string or dictionary, defaults to `''`)

This allows you to tell `;;` which flags can be used by the command. An error
message will be printed if the user tries to use an invalid flag. See the
[Special arguments](#special-arguments) section above for more information about flags.  
You can use a string, like `'ab'`, or a dictionary if you'd like to add information:  
`{'a': 'Does a certain action', 'b': 'Executes plan B'}`  
See the [Documenting your command](#documenting-your-command) for details about documentation.

### Special functions

Cogs aren't made of commands only: you can have functions execute upon
loading/unloading of a cog, or even based on events (see below).  
This is done by using special decorators:

#### `@cog.init`

Any function decorated with this will be called when the cog is loaded.
You can only have one init function.

#### `@cog.exit`

Any function decorated with this will be called when the cog is unloaded.
You can only have one exit function.

### Event handlers

You want to do even more stuff? As of [v0.2.1], you can write custom event
handlers! Those are the same events you can use in a `discord.py` client, except
you register them using `@cog.event`. The best part is, you can use a bunch of
special arguments and it'll likely
work as intended!

```python
@cog.event
def on_typing(user):
    return 'I see you, ' + user.display_name
```

The standard `on_typing` event uses `(channel, user, when)` but you can directly
ask for whatever you need! And just like commands, you can simply return what
you want to send.

> Side note: returning a message will only work if the event takes place in a
> specific channel. For example, on_reaction_add will work but not on_member_update.

### Using your cog

As written above, you just need to drop it in the `cogs` folder!

> Side note: make sure you have the `import gearbox; cog = gearbox.Cog('name')` part,
> otherwise `;;` will consider the file broken and won't load it until it restarts.

If `;;` is running, it'll automatically load it within a couple of seconds, and
reload it when you edit it. Don't worry, if you break stuff, it'll keep running
the old code until the new one is working.  
If you have name conflicts with another module, call your commands
with `cog_name.command_name` to avoid collisions.

[v0.1.0]: https://github.com/Zeroji/semicolon/releases/tag/v0.1.0
[v0.1.1]: https://github.com/Zeroji/semicolon/releases/tag/v0.1.1
[v0.1.2]: https://github.com/Zeroji/semicolon/releases/tag/v0.1.2
[v0.1.3]: https://github.com/Zeroji/semicolon/releases/tag/v0.1.3
[v0.1.4]: https://github.com/Zeroji/semicolon/releases/tag/v0.1.4
[v0.2.0]: https://github.com/Zeroji/semicolon/releases/tag/v0.2.0
[latest]: https://github.com/Zeroji/semicolon/releases/latest
