import asyncio
import os
import re
import better_profanity
import emoji
import nude
import requests
from better_profanity import profanity
from google_trans_new import google_translator
from telethon import events
from telethon.tl.types import ChatBannedRights
from Marie.confing import get_int_key, get_str_key
from Marie.services.telethonbasics import is_admin
from Marie.events import register
from pymongo import MongoClient
from Marie.modules.sql.nsfw_watch_sql import (
    add_nsfwatch,
    get_all_nsfw_enabled_chat,
    is_nsfwatch_indb,
    rmnsfwatch,
)
from Marie import telethn as tbot, MONGO_DB_URI, BOT_ID

translator = google_translator()
MUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=False)

MONGO_DB_URI = get_str_key("MONGO_DB_URI")

client = MongoClient()
client = MongoClient(MONGO_DB_URI)
db = client["Marie"]

async def is_nsfw(event):
    lmao = event
    if not (
        lmao.gif
        or lmao.video
        or lmao.video_note
        or lmao.photo
        or lmao.sticker
        or lmao.media
    ):
        return False
    if lmao.video or lmao.video_note or lmao.sticker or lmao.gif:
        try:
            starkstark = await event.client.download_media(lmao.media, thumb=-1)
        except:
            return False
    elif lmao.photo or lmao.sticker:
        try:
            starkstark = await event.client.download_media(lmao.media)
        except:
            return False
    img = starkstark
    f = {"file": (img, open(img, "rb"))}

    r = requests.post("https://starkapi.herokuapp.com/nsfw/", files=f).json()
    if r.get("success") is False:
        is_nsfw = False
    elif r.get("is_nsfw") is True:
        is_nsfw = True
    elif r.get("is_nsfw") is False:
        is_nsfw = False
    return is_nsfw


@tbot.on(events.NewMessage(pattern="/gshield (.*)"))
async def nsfw_watch(event):
    if not event.is_group:
        await event.reply("You Can Only NSFW Watch In Groups.")
        return
    input_str = event.pattern_match.group(1)
    if not await is_admin(event, BOT_ID):
        await event.reply("`I Should Be Admin To Do This !`")
        return
    if await is_admin(event, event.message.sender_id):
        if (
            input_str == "on"
            or input_str == "On"
            or input_str == "ON"
            or input_str == "enable"
        ):
            if is_nsfwatch_indb(str(event.chat_id)):
                await event.reply("`This Chat Has Already Enabled NSFW Watch.`")
                return
            add_nsfwatch(str(event.chat_id))
            await event.reply(
                f"**Added Chat {event.chat.title} With ID {event.chat_id} This Groups NSFW Contents Will Be Deleted**"
            )
        elif (
            input_str == "off"
            or input_str == "Off"
            or input_str == "OFF"
            or input_str == "disable"
        ):
            if not is_nsfwatch_indb(str(event.chat_id)):
                await event.reply("This Chat Has Not Enabled NSFW Watch.")
                return
            rmnsfwatch(str(event.chat_id))
            await event.reply(
                f"**Removed Chat {event.chat.title} With ID {event.chat_id} From NSFW Watch**"
            )
        else:
            await event.reply(
                "I Understand `/nsfwguardian on` And `/nsfwguardian off` Only"
            )
    else:
        await event.reply("`You Should Be Admin To Do This!`")
        return


approved_users = db.approve
spammers = db.spammer
globalchat = db.globchat

CMD_STARTERS = ["/", "!", "."]
profanity.load_censor_words_from_file("./profanity_wordlist.txt")


@register(pattern="^/profanity(?: |$)(.*)")
async def profanity(event):
    if event.fwd_from:
        return
    if not event.is_group:
        await event.reply("You Can Only Profanity In Groups.")
        return
    event.pattern_match.group(1)
    if not await is_admin(event, BOT_ID):
        await event.reply("`I Should Be Admin To Do This!`")
        return
    if await is_admin(event, event.message.sender_id):
        input = event.pattern_match.group(1)
        chats = spammers.find({})
        if not input:
            for c in chats:
                if event.chat_id == c["id"]:
                    await event.reply(
                        "Please Provide Some Input Yes Or No.\n\nCurrent Setting Is : **on** ."
                    )
                    return
            await event.reply(
                "Please Provide Some Input Yes Or No.\n\nCurrent Setting Is : **off** ."
            )
            return
        if input == "on":
            if event.is_group:
                chats = spammers.find({})
                for c in chats:
                    if event.chat_id == c["id"]:
                        await event.reply(
                            "Profanity Filter Is Already Activated For This Chat."
                        )
                        return
                spammers.insert_one({"id": event.chat_id})
                await event.reply("Profanity Filter Turned On For This Chat.")
        if input == "off":
            if event.is_group:
                chats = spammers.find({})
                for c in chats:
                    if event.chat_id == c["id"]:
                        spammers.delete_one({"id": event.chat_id})
                        await event.reply("Profanity Filter Turned Off For This Chat.")
                        return
            await event.reply("Profanity Filter Isn't Turned On For This Chat.")
        if not input == "on" and not input == "off":
            await event.reply("I Only Understand By On Or Off")
            return
    else:
        await event.reply("`You Should Be Admin To Do This!`")
        return


@register(pattern="^/globalmode(?: |$)(.*)")
async def profanity(event):
    if event.fwd_from:
        return
    if not event.is_group:
        await event.reply("You Can Only Enable Global Mode Watch In Groups.")
        return
    event.pattern_match.group(1)
    if not await is_admin(event, BOT_ID):
        await event.reply("`I Should Be Admin To Do This!`")
        return
    if await is_admin(event, event.message.sender_id):

        input = event.pattern_match.group(1)
        chats = globalchat.find({})
        if not input:
            for c in chats:
                if event.chat_id == c["id"]:
                    await event.reply(
                        "Please Provide Some Input Yes Or No.\n\nCurrent Setting Is : **on** ."
                    )
                    return
            await event.reply(
                "Please Provide Some Input Yes Or No.\n\nCurrent Setting Is : **off** ."
            )
            return
        if input == "on":
            if event.is_group:
                chats = globalchat.find({})
                for c in chats:
                    if event.chat_id == c["id"]:
                        await event.reply(
                            "Global Mode Already Activated For This Chat."
                        )
                        return
                globalchat.insert_one({"id": event.chat_id})
                await event.reply("Global Mode Turned On For This Chat.")
        if input == "off":
            if event.is_group:
                chats = globalchat.find({})
                for c in chats:
                    if event.chat_id == c["id"]:
                        globalchat.delete_one({"id": event.chat_id})
                        await event.reply("Global Mode Turned Off For This Chat.")
                        return
            await event.reply("Global mode isn't turned on for this chat .")
        if not input == "on" and not input == "off":
            await event.reply("I Only Understand By On Or Off")
            return
    else:
        await event.reply("`You Should Be Admin To Do This!`")
        return


@tbot.on(events.NewMessage(pattern=None))
async def del_profanity(event):
    if event.is_private:
        return
    msg = str(event.text)
    sender = await event.get_sender()
    # let = sender.username
    if await is_admin(event, event.message.sender_id):
        return
    chats = spammers.find({})
    for c in chats:
        if event.text:
            if event.chat_id == c["id"]:
                if better_profanity.profanity.contains_profanity(msg):
                    await event.delete()
                    if sender.username is None:
                        st = sender.first_name
                        hh = sender.id
                        final = f"[{st}](tg://user?id={hh}) **{msg}** Is Detected As A Slang Word And Your Message Has Been Deleted"
                    else:
                        final = f"Sir **{msg}** Is Detected As A Slang Word And Your Message Has Been Deleted"
                    dev = await event.respond(final)
                    await asyncio.sleep(10)
                    await dev.delete()
        if event.photo:
            if event.chat_id == c["id"]:
                await event.client.download_media(event.photo, "nudes.jpg")
                if nude.is_nude("./nudes.jpg"):
                    await event.delete()
                    st = sender.first_name
                    hh = sender.id
                    final = f"**ɴꜱꜰᴡ ᴅᴇᴛᴇᴄᴛᴇᴅ**\n\n{st}](tg://user?id={hh}) Your Massage Contain NSFW Content... So, Marie Deleted The Massage \n\n **NSFW Sender - User / Bot :** {st}](tg://user?id={hh})  \n\n`Automatic Detections Powered By Marie-AI` \n**#Group_Guardian** "
                    dev = await event.respond(final)
                    await asyncio.sleep(10)
                    await dev.delete()
                    os.remove("nudes.jpg")
def extract_emojis(s):
    return "".join(c for c in s if c in emoji.UNICODE_EMOJI)


@tbot.on(events.NewMessage(pattern=None))
async def del_profanity(event):
    if event.is_private:
        return
    msg = str(event.text)
    sender = await event.get_sender()
    # sender.username
    if await is_admin(event, event.message.sender_id):
        return
    chats = globalchat.find({})
    for c in chats:
        if event.text:
            if event.chat_id == c["id"]:
                u = msg.split()
                emj = extract_emojis(msg)
                msg = msg.replace(emj, "")
                if (
                    [(k) for k in u if k.startswith("@")]
                    and [(k) for k in u if k.startswith("#")]
                    and [(k) for k in u if k.startswith("/")]
                    and re.findall(r"\[([^]]+)]\(\s*([^)]+)\s*\)", msg) != []
                ):
                    h = " ".join(filter(lambda x: x[0] != "@", u))
                    km = re.sub(r"\[([^]]+)]\(\s*([^)]+)\s*\)", r"", h)
                    tm = km.split()
                    jm = " ".join(filter(lambda x: x[0] != "#", tm))
                    hm = jm.split()
                    rm = " ".join(filter(lambda x: x[0] != "/", hm))
                elif [(k) for k in u if k.startswith("@")]:
                    rm = " ".join(filter(lambda x: x[0] != "@", u))
                elif [(k) for k in u if k.startswith("#")]:
                    rm = " ".join(filter(lambda x: x[0] != "#", u))
                elif [(k) for k in u if k.startswith("/")]:
                    rm = " ".join(filter(lambda x: x[0] != "/", u))
                elif re.findall(r"\[([^]]+)]\(\s*([^)]+)\s*\)", msg) != []:
                    rm = re.sub(r"\[([^]]+)]\(\s*([^)]+)\s*\)", r"", msg)
                else:
                    rm = msg
                # print (rm)
                b = translator.detect(rm)
                if not "en" in b and not b == "":
                    await event.delete()
                    st = sender.first_name
                    hh = sender.id
                    final = f"[{st}](tg://user?id={hh}) You Should Only Speak English Here!"
                    dev = await event.respond(final)
                    await asyncio.sleep(10)
                    await dev.delete()

__mod_name__ = "Shield"
