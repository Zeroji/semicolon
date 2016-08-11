## How to write your cog

`;;` draws its main features from modules, named "cogs".  
Writing one is rather straightforward, but a couple rules have to be respected.

### Match `[a-z][a-z_0-9]*\.py`

Don't run away ~~yet~~! This simply means that the name of your file must be **full lowercase** and it has to start by a letter (any file starting with `_` or a digit will be ignored). Once you have that file, just drop it in the `cogs` folder and that's all.

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

Straightforward, right? Your command just have to return something, and `;;` will send it in the good channel. If you return nothing... Well, nothing happens.  
But what if you want it to greet someone specifically?

#### Special arguments

Greeting a user can be done very simply:

```python
@cog.command
def hello(author):
    return 'Hello, %s!' % author.name
```

> If you really aren't familiar with `discord.py`, have a look at [their documentation](http://discordpy.readthedocs.io/en/latest/). For very simple usage, you can get a user/channel/server name with `.name`.

> Wondering what this `%` thing does? Basically, it's the same as `'Hello, ' + author.name + '!'` but shorter and fancier.
[Learn more here](https://docs.python.org/3.5/library/stdtypes.html#printf-style-string-formatting)

As you can see, simply putting `author` in the function definition will give you the corresponding object. Why? Because `;;` is made in such a way that it'll look at what you want, and attempt to provide it to you so you don't need to write extra pieces of code. Here's a list of those "special" arguments: *(as of v0.1.0)*

|Argument  | Description
|-
|`client`  | The application's `discord.Client()`
|`message` | The Message object which was sent - don't use like a string!
|`author`  | Shortcut for `message.author`
|`channel` | Shortcut for `message.channel`
|`server`  | Shortcut for `message.server`

*Remember that using those will give you special values, which might not correspond to your expectations.*

#### Normal arguments

Now maybe you simply want to write a `repeat` command, but you don't know how to get the text? Just ask for it!

```python
@cog.command
def repeat(what_they_said):
    return what_they_said
```

When sending arguments to commands, `;;` will take care of special arguments, then send the rest of the message to the other arguments. If you need multiple arguments, just define them!

```python
@cog.command
def add(number_a, number_b):
    return str(int(number_a) + int(number_b))
```

> *May change in future versions*  
If the user doesn't provide the arguments you need, for example if they type `add 4`, `;;` will send an empty string (`''`) for each missing arguments.

> If the user sends too many arguments, for example by typing `add 1 2 3`, then your last argument will receive the extra information. Here, `number_a` would contain `'1'` but `number_b` would contain `'2 3'`. You can discard unwanted information by adding a third argument which will take it:
```python
def add(number_a, number_b, trash):
```

#### More arguments!

Let's say you want to have a command that takes a string, then a series of strings, and inserts that first string between all the others, i.e. `, 1 2 3` would give `1,2,3` - wow, that's just like `str.join()`!  
You'll want to have the first argument, then "all the rest". Of course, you could get away with using `def join(my_string, all_the_rest):` and then use `.split()`, but ;; can do that for you! Simply add `*` before your last argument, and it'll receive a nice little list of whatever was sent:

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

No, this isn't about adding a cute little ribbon onto it. *(as of v0.1.0)*

You've already used the decorator `@cog.command` to indicate that your function was a `;;` command and not a random function.  
You can do a bit more, here, have a list:

##### `@cog.rename(name)`
This will change the name of your command. It's useful, for example, if you want your command to be called `str` but you can't because of Python's `str()` function. Just call your function `asdf` and put `@cog.rename('str')` before it.

##### `@cog.alias(alias, ...)`
This creates aliases for your command. Let's say you find `encrypt` is a quite long name, just add `@cog.alias('en')` and you'll be able to call your command with `encrypt` *and* `en`.

##### `@cog.init`
This doesn't apply to a command, but to a regular function - it marks it, so it will be called when the cog is loaded. You can only have one init function.
> *Not yet implemented as of v0.1.0*

##### `@cog.exit`
This doesn't apply to a command, but to a regular function - it marks it, so it will be called when the cog is unloaded. You can only have one exit function.
> *Not yet implemented as of v0.1.0*

### Using your cog

As written above, you just need to drop it in the `cogs` folder!  
If `;;` is running, it'll automatically load it within a couple of seconds, and reload it when you edit it. Don't worry, if you break stuff, it'll keep running the old code until the new one is working.  
If you have name conflicts with another module, call your commands with `cog_name.command_name` to avoid collisions.
