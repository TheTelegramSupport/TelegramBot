from geopy.geocoders import Nominatim
from telethon import *
from telethon.tl import *

from Marie import *
from Marie import telethn as tbot
from Marie.events import register

GMAPS_LOC = "https://maps.googleapis.com/maps/api/geocode/json"


@register(pattern="^/gps (.*)")
async def _(event):
    args = event.pattern_match.group(1)

    try:
        geolocator = Nominatim(user_agent="SkittBot")
        location = args
        geoloc = geolocator.geocode(location)
        longitude = geoloc.longitude
        latitude = geoloc.latitude
        gm = "https://www.google.com/maps/search/{},{}".format(latitude, longitude)
        await tbot.send_file(
            event.chat_id,
            file=types.InputMediaGeoPoint(
                types.InputGeoPoint(float(latitude), float(longitude))
            ),
        )
        await event.reply(
            "Here Is Your ReQuired Location You Can Find It By Clicking Here: [Here]({}) ..".format(gm),
            link_preview=False,
        )
    except Exception as e:
        print(e)
        await event.reply("I Am Unable To Find That Sorry")


__help__ = """
 » /gps <location>*:* Gets You, Your Desired Location.
"""

__mod_name__ = "Gps"
