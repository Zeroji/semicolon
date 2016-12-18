"""Games cog"""
import gearbox
cog = gearbox.Cog()
_ = cog.gettext


@cog.command
def test():
    """Example command inside a cog containing sub-cogs."""
    return _('This command works!')
