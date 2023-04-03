import html
import json
import re
from time import sleep

import requests
from telegram import (
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    Update,
    User,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    run_async,
)
from telegram.utils.helpers import mention_html

import Marie.modules.sql.chatbot_sql as sql
from Marie import BOT_ID, BOT_USERNAME, BOT_NAME, dispatcher
from Marie.modules.helper_funcs.chat_status import user_admin, user_admin_no_reply
from Marie.modules.log_channel import gloggable


@run_async
@user_admin_no_reply
@gloggable
def alonerm(update: Update, context: CallbackContext) -> str:
    query: Optional[CallbackQuery] = update.callback_query
    user: Optional[User] = update.effective_user
    match = re.match(r"rm_chat\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat: Optional[Chat] = update.effective_chat
        is_alone = sql.set_alone(chat.id)
        if is_alone:
            is_alone = sql.set_alone(user_id)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"AI_Disable\n"
                f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            )
        else:
            update.effective_message.edit_text(
                "{} Chatbot Disabled By {} .".format(
                    dispatcher.bot.first_name, mention_html(user.id, user.first_name)
                ),
                parse_mode=ParseMode.HTML,
            )

    return ""


@run_async
@user_admin_no_reply
@gloggable
def aloneadd(update: Update, context: CallbackContext) -> str:
    query: Optional[CallbackQuery] = update.callback_query
    user: Optional[User] = update.effective_user
    match = re.match(r"add_chat\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat: Optional[Chat] = update.effective_chat
        is_alone = sql.rem_alone(chat.id)
        if is_alone:
            is_alone = sql.rem_alone(user_id)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"AI_Enable\n"
                f"<b>Admin :</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            )
        else:
            update.effective_message.edit_text(
                "{} Chatbot enabled By{} .".format(
                    dispatcher.bot.first_name, mention_html(user.id, user.first_name)
                ),
                parse_mode=ParseMode.HTML,
            )

    return ""


@run_async
@user_admin
@gloggable
def alone(update: Update, context: CallbackContext):
    message = update.effective_message
    msg = "Choose An Option To Enable/Disable Chatbot"
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="Enable", callback_data="add_chat({})"),
                InlineKeyboardButton(text="Disable", callback_data="rm_chat({})"),
            ],
        ]
    )
    message.reply_text(
        text=msg,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


def alone_message(context: CallbackContext, message):
    reply_message = message.reply_to_message
    if message.text.lower() == "alone":
        return True
    elif BOT_USERNAME in message.text.upper():
        return True
    elif reply_message:
        if reply_message.from_user.id == BOT_ID:
            return True
    else:
        return False


def chatbot(update: Update, context: CallbackContext):
    message = update.effective_message
    chat_id = update.effective_chat.id
    bot = context.bot
    is_alone = sql.is_alone(chat_id)
    if is_alone:
        return

    if message.text and not message.document:
        if not alone_message(context, message):
            return
        kristu = message.text
        bot.send_chat_action(chat_id, action="typing")
        url = f"https://kora-api.vercel.app/chatbot/2d94e37d-937f-4d28-9196-bd5552cac68b/{BOT_NAME}/Anonymous/message={Marie}"
        request = requests.get(url)
        results = json.loads(request.text)
        sleep(0.5)
        message.reply_text(results["reply"])


__help__ = """
  »  /chatbot *:* An AI Bot Features Will Talk To You
"""

__mod_name__ = "ChatBot"


CHATBOTK_HANDLER = CommandHandler("chatbot", alone)
ADD_CHAT_HANDLER = CallbackQueryHandler(aloneadd, pattern=r"add_chat")
RM_CHAT_HANDLER = CallbackQueryHandler(alonerm, pattern=r"rm_chat")
CHATBOT_HANDLER = MessageHandler(
    Filters.text
    & (~Filters.regex(r"^#[^\s]+") & ~Filters.regex(r"^!") & ~Filters.regex(r"^\/")),
    chatbot,
)

dispatcher.add_handler(ADD_CHAT_HANDLER)
dispatcher.add_handler(CHATBOTK_HANDLER)
dispatcher.add_handler(RM_CHAT_HANDLER)
dispatcher.add_handler(CHATBOT_HANDLER)

__handlers__ = [
    ADD_CHAT_HANDLER,
    CHATBOTK_HANDLER,
    RM_CHAT_HANDLER,
    CHATBOT_HANDLER,
]
