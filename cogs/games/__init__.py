"""Games cog"""
import gearbox
cog = gearbox.Cog('games')


@cog.command
def test():
    """Example command inside a cog containing sub-cogs."""
    return 'This command works!'
