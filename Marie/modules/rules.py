from typing import Optional

import Marie.modules.sql.rules_sql as sql
from Marie import dispatcher
from Marie.modules.helper_funcs.chat_status import user_admin
from Marie.modules.helper_funcs.string_handling import markdown_parser
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ParseMode,
    Update,
    User,
)
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters
from telegram.utils.helpers import escape_markdown


def get_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    send_rules(update, chat_id)


# Do not async - not from a handler
def send_rules(update, chat_id, from_pm=False):
    bot = dispatcher.bot
    user = update.effective_user  # type: Optional[User]
    reply_msg = update.message.reply_to_message
    try:
        chat = bot.get_chat(chat_id)
    except BadRequest as excp:
        if excp.message == "chat not found" and from_pm:
            bot.send_message(
                user.id,
                "The Rules Shortcut For This Chat Hasn't Been Set Properly! Ask Admins ...Okay!"
                "Fix This.\nMaybe They Forgot The Hyphen In ID ",
            )
            return
        raise

    rules = sql.get_rules(chat_id)
    text = f"ᴛʜᴇ ʀᴜʟᴇꜱ ꜰᴏʀ The Rules For *{escape_markdown(chat.title)}* Are:\n\n{rules}"

    if from_pm and rules:
        bot.send_message(
            user.id,
            text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
    elif from_pm:
        bot.send_message(
            user.id,
            "The Group Admins Hasn't Set Any Rules For This Chat Yet. "
            "This Probably Doesn't Mean Its Lawless Though...! ",
        )
    elif rules and reply_msg:
        reply_msg.reply_text(
            "Please Click The Button Below To See The Rules.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Rules",
                            url=f"t.me/{bot.username}?start={chat_id}",
                        ),
                    ],
                ],
            ),
        )
    elif rules:
        update.effective_message.reply_text(
            "Please Click The Button Below To See The Rules.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Rules",
                            url=f"t.me/{bot.username}?start={chat_id}",
                        ),
                    ],
                ],
            ),
        )
    else:
        update.effective_message.reply_text(
            "The Group Admins Hasn't Set Any Rules For This Chat Yet . "
            "This Probably Doesn't Mean Its Lawless Though...!",
        )


@user_admin
def set_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    raw_text = msg.text
    args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
    if len(args) == 2:
        txt = args[1]
        offset = len(txt) - len(raw_text)  # set correct offset relative to command
        markdown_rules = markdown_parser(
            txt,
            entities=msg.parse_entities(),
            offset=offset,
        )

        sql.set_rules(chat_id, markdown_rules)
        update.effective_message.reply_text("Successfully Set Rules For This Group.")


@user_admin
def clear_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    sql.set_rules(chat_id, "")
    update.effective_message.reply_text("Successfully Cleared Rules!")


def __stats__():
    return f"× {sql.num_chats()} Chats Have Rules Set."


def __import_data__(chat_id, data):
    # set chat rules
    rules = data.get("info", {}).get("rules", "")
    sql.set_rules(chat_id, rules)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"This Chat Has Had It's Rules Set: `{bool(sql.get_rules(chat_id))}` "


__mod_name__ = "Rules"

GET_RULES_HANDLER = CommandHandler(
    "rules", get_rules, filters=Filters.chat_type.groups, run_async=True
)
SET_RULES_HANDLER = CommandHandler(
    "setrules", set_rules, filters=Filters.chat_type.groups, run_async=True
)
RESET_RULES_HANDLER = CommandHandler(
    "clearrules", clear_rules, filters=Filters.chat_type.groups, run_async=True
)

dispatcher.add_handler(GET_RULES_HANDLER)
dispatcher.add_handler(SET_RULES_HANDLER)
dispatcher.add_handler(RESET_RULES_HANDLER)
