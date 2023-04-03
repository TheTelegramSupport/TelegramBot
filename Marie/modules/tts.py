from typing import Optional, List
from gtts import gTTS
import os
import requests
import json

from telegram import ChatAction
from telegram.ext import run_async

from Marie import dispatcher
from Marie.modules.disable import DisableAbleCommandHandler
from Marie.modules.helper_funcs.alternate import typing_action, send_action

@run_async
@send_action(ChatAction.RECORD_AUDIO)
def gtts(update, context):
    msg = update.effective_message
    reply = " ".join(context.args)
    if not reply:
        if msg.reply_to_message:
            reply = msg.reply_to_message.text
        else:
            return msg.reply_text(
                "Reply To Some Message Or Enter Some Text To Convert It Into Audio Format!"
            )
        for x in "\n":
            reply = reply.replace(x, "")
    try:
        tts = gTTS(reply)
        tts.save("k.mp3")
        with open("k.mp3", "rb") as speech:
            msg.reply_audio(speech)
    finally:
        if os.path.isfile("k.mp3"):
            os.remove("k.mp3")
            
dispatcher.add_handler(DisableAbleCommandHandler("tts", gtts, pass_args=True))

__help__ = """
 » `/tts` <reply to msg> :  Turns Text To Speech 
 """
__mod_name__ = "Tts"
