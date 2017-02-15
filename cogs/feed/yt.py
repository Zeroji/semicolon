"""Youtube feed notifier."""
import json
import arrow
import gearbox
cog = gearbox.Cog()


LANG = 'en_US'
ZONE = 'Europe/Paris'
_ = lambda s: s


@cog.on_socket(b'hook/youtube/')
async def publish_video(client, data_str, socket):
    data = json.loads(data_str)
    for video in data['items']:
        author = video['actor']['displayName']
        short_url = 'http://youtu.be/' + video['id'].split(':', 2)[2]
        published = arrow.get(video['published'])
        message = _('New video from **{author}**: {short_url} {time_ago} ({time})').format(
            author=author, short_url=short_url, time_ago=published.humanize(locale=LANG),
            time=published.to(ZONE).format(_('HH:mm'))
        )
        await client.send_message(client.get_channel('272463984026976257'), message)
