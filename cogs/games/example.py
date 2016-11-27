"""Sub-cog example."""
import gearbox
cog = gearbox.Cog('example')


@cog.command
def example(author):
    """Sub-cog command example."""
    return f"Hi {author.name}, I'm a working example!"
