"""XKCD feed notifier."""
import html
import json
import discord
import gearbox
cog = gearbox.Cog()


@cog.on_socket(b'hook/xkcd/')
async def display_xkcd(client, data_str, socket):
    data = json.loads(data_str)
    for xkcd in data['items']:
        id = xkcd['id'].split('/')[3]
        title = xkcd['title']
        url = xkcd['permalinkUrl']
        summary = xkcd['summary']
        image_url_start = summary.find('<img src="')
        image_url_end = summary.find('" title="', image_url_start)
        image_url = summary[image_url_start + len('<img src="'):image_url_end]
        image_title_end = summary.find('" alt="', image_url_end)
        alt_text = summary[image_url_end + len('" title="'):image_title_end]
        embed = discord.Embed(title='XKCD #{id}: {title}'.format(id=id, title=title),
                              url=url,
                              description=html.unescape(alt_text))
        embed.set_image(url=image_url)
        await client.get_channel('272463984026976257').send(embed=embed)
