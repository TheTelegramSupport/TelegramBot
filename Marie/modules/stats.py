import os
import asyncio

from pyrogram import filters
from pyrogram.types import Message
from pymongo import MongoClient
from Marie import pbot
from Marie.db import MONGO_URL as db_url

users_db = MongoClient(db_url)['users']
col = users_db['USER']
grps = users_db['GROUPS']


@pbot.on_message(filters.command("stats"))
async def stats(_, m: Message):
    users = col.find({})
    mfs = []
    for x in users:
        mfs.append(x['user_id'])

    total = len(mfs)

    grp = grps.find({})
    grps_ = []
    for x in grp:
        grps_.append(x['chat_id'])

    total_ = len(grps_)

    await m.reply_text(f"👥 Total Users: `{total}`\n💭 Total Groups: `{total_}`")

    
    __help__ = """
 » `/stats` :  Gives Information About Your Bot
 """
    __mod_name__ = "Stats"
