# Translations

As you may have noticed, `;;` is written in English. However, it can support
multiple languages, if there are available translations.

## Language settings

If you are a server owner, or if you have the "Manage server" permission on a
server, you can use the command `lang` to display available languages and
change the server language.

Usage: `settings.lang [language]`  

> Currently, language codes ('en', 'fr', ...) are used, but greater flexibility will come soon

## Create a translation

Want to help translate `;;`? You're welcome!  
If you look in the folder `locale/templates/`, you'll see a handful of files
with the extension `.pot`: these are **translation templates**. With a software
like [Poedit](https://poedit.net/), you can open a translation template, fill
in the blanks and save it as a pair of `.mo` and `.po` files.

To help translating `;;`, pick a `.pot` files in `locale/templates/`, translate
it into your language and put it in `locale/[LANG]/LC_MESSAGES`: if you picked
`locale/templates/example/games.pot` and you translated it to Italian, you
should end up with `locale/it_IT/LC_MESSAGES/example/games.mo`.

Once this is done, start `;;` and `lang` should show the language you added.
If you switch to it, messages from the cog you translated should be in your
language!

### Contributing

If you want to push your translations to GitHub, fine, but make sure you
follow those guidelines:

- You should upload both `.mo` and `.po` files, `.mo` are used by the program,
  and `.po` allow other people to update your work
- Your files should have the same name as the templates they were made from:
  `locale/templates/a/b/c.pot` should give `locale/[LANG]/LC_MESSAGES/a/b/c.po`
- It is recommended you use the `language_COUNTRY` notation, for example `fr_FR`,
  `en_GB` or `en_UK`

## Make your cog translatable

Now, if as a developer you want to make your cog translatable by other people,
it's fairly easy.

### Translation functions

`;;` uses the `gettext` module for translations. It's quite very simplified
here, so just use the following at the top of your cog:

```python
import gearbox
cog = gearbox.Cog()
_ = cog.gettext
```

You can also add the `ngettext` function if needed (see below) with
the following line:

```python
ngettext = cog.ngettext
```

### Mark strings to be translated

The `_` function performs white magic to translate your strings into whatever
is currently needed. When you have some translatable text, just wrap it with it:

```python
@cog.command
def hello():
    return _('Hello, world!')
```

The `ngettext` function is a bit more complicated, and is used for singular/plural
translations. It takes a singular string, plural string, and the corresponding number:

```python
@cog.command
def apples(count: int):
    return ngettext('I have {count} apple',
                    'I have {count} apples',
                    count).format(count=count)
```

This will pick one of the other string depending on `count`, and format it to insert
the number `count` inside it. It's mostly required for grammatical reasons.

### Generate translation templates

If you have a Linux-based bash with `xgettext` on your system, just navigate to
the folder containing `;;` and execute `./templates.sh`: it will generate translation
templates for every cog you have. Pretty simple.

Otherwise, you can use the `pygettext` utility, available through `pip`, but it might
be outdated: make sure it can work properly with `ngettext` or you'll have issues.

`pygettext -o locale/templates/awesome_cog.pot cogs/awesome_cog.py`
