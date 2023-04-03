import os
import wget
import urllib.request
from faker import Faker
import pyaztro
from faker.providers import internet
from Marie import dispatcher
from Marie.modules.disable import DisableAbleCommandHandler
from telegram import Update, ParseMode
from telegram.ext import CallbackContext, run_async


def fakeid(update: Update, context: CallbackContext):
    message = update.effective_message
    dltmsg = message.reply_text("Generating Fake Identity For You...")
    fake = Faker()
    print("Fake Details Generated\n")
    name = str(fake.name())
    fake.add_provider(internet)
    address = str(fake.address())
    ip = fake.ipv4_private()
    cc = fake.credit_card_full()
    email = fake.ascii_free_email()
    job = fake.job()
    android = fake.android_platform_token()
    pc = fake.chrome()
    message.reply_text(
        f"<b> Fake Information Generated</b>\n<b>Name :-</b><code>{name}</code>\n\n<b>Address:-</b><code>{address}</code>\n\n<b>IP Address:-</b><code>{ip}</code>\n\n<b>Credit Card:-</b><code>{cc}</code>\n\n<b>Email ID:-</b><code>{email}</code>\n\n<b>Job:-</b><code>{job}</code>\n\n<b>Android User Agent:-</b><code>{android}</code>\n\n<b>Pc User Agent:-</b><code>{pc}</code>",
        parse_mode=ParseMode.HTML,
    )

    dltmsg.delete()




def astro(update: Update, context: CallbackContext):
    message = update.effective_message
    args = message.text.split(" ", 1)
    
    if len(args) == 1:
        message.reply_text('Please Choose Your Horoscope Sing. List Of All Sings - Aries, Taurus, Gemini, Cancer, Leo, Virgo, Libra, Scorpio, Sagittarius, Carpicorn, Aquarius And Pisces.')
        return
    else:
        pass
    msg = message.reply_text("Fetching Data...")
    try:
        x = args[1]
        horoscope = pyaztro.Aztro(sign=x)
        mood = horoscope.mood
        lt = horoscope.lucky_time
        desc = horoscope.description
        col = horoscope.color
        com = horoscope.compatibility
        ln = horoscope.lucky_number

        result = (
            f"**Horoscope For `{x}`**:\n"
            f"**Mood :** `{mood}`\n"
            f"**Lucky Time :** `{lt}`\n"
            f"**Lucky Colour :** `{col}`\n"
            f"**Lucky Number :** `{ln}`\n"
            f"**Compatibility :** `{com}`\n"
            f"**Description :** `{desc}`\n"
        )

        msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        msg.edit_text(f"Sorry I Haven't Found Anything!\nMaybe You Have Given A wrong Sing Name Please Check Help Of Horoscope.\nError - {e} ..")



__help__ = """
 » `/hs <Zodiac-Sings>`:
Usage: It Will Show Horoscope Of Daily Of Your Sing.
List Of All Signs - Aries, Taurus, Gemini, Cancer, Leo, Virgo, Libra, Scorpio, Sagittarius, Carpicorn, Aquarius And Piece.
 » `/fakeid`:
Usage: It Will Create Fake Identity For You.
"""

__mod_name__ = "Identity"

FAKER_HANDLER = DisableAbleCommandHandler("fakeid", fakeid, run_async=True)
ASTRO_HANDLER = DisableAbleCommandHandler("hs", astro, run_async=True)
dispatcher.add_handler(FAKER_HANDLER)
dispatcher.add_handler(ASTRO_HANDLER)
