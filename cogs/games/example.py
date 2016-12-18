"""Sub-cog example."""
import gearbox
cog = gearbox.Cog()
_ = cog.gettext


@cog.command
def example(author):
    """Sub-cog command example."""
    return _("Hi {name}, I'm a working example!").format(name=author.name)
