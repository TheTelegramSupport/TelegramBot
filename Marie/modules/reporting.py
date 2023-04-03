import html

from Marie import LOGGER, DRAGONS, TIGERS, WOLVES, dispatcher
from Marie.modules.helper_funcs.chat_status import user_admin, user_not_admin
from Marie.modules.log_channel import loggable
from Marie.modules.sql import reporting_sql as sql
from telegram import Chat, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import BadRequest, Unauthorized
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    run_async,
)
from telegram.utils.helpers import mention_html

REPORT_GROUP = 12
REPORT_IMMUNE_USERS = DRAGONS + TIGERS + WOLVES



@user_admin
def report_setting(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    msg = update.effective_message

    if chat.type == chat.PRIVATE:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_user_setting(chat.id, True)
                msg.reply_text(
                    "Turned On Reporting! You'll Be Notified Whenever Anyone Reports Something.",
                )

            elif args[0] in ("no", "off"):
                sql.set_user_setting(chat.id, False)
                msg.reply_text("Turned Off Reporting! You Won't Get Any Reports.")
        else:
            msg.reply_text(
                f"Your Current Report Preference Is: `{sql.user_should_report(chat.id)}` ..",
                parse_mode=ParseMode.MARKDOWN,
            )

    elif len(args) >= 1:
        if args[0] in ("yes", "on"):
            sql.set_chat_setting(chat.id, True)
            msg.reply_text(
                "Turned On Reporting! Admins Who Have Turned On Reports Will Be Notified When /report "
                "Or @admin Is Called .",
            )

        elif args[0] in ("no", "off"):
            sql.set_chat_setting(chat.id, False)
            msg.reply_text(
                "Turned Off Reporting! No Admins Will Be Notified On /report Or @admin .",
            )
    else:
        msg.reply_text(
            f"This Group's Current Setting Is: `{sql.chat_should_report(chat.id)}` ..",
            parse_mode=ParseMode.MARKDOWN,
        )



@user_not_admin
@loggable
def report(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if chat and message.reply_to_message and sql.chat_should_report(chat.id):
        reported_user = message.reply_to_message.from_user
        chat_name = chat.title or chat.first or chat.username
        admin_list = chat.get_administrators()
        message = update.effective_message

        if user.id == reported_user.id:
            message.reply_text("Uh Yeah, Sure Sure.....Maso Much?")
            return

        elif user.id == bot.id:
            message.reply_text("Yeah, Nice Try......")
            return

        elif reported_user.id in REPORT_IMMUNE_USERS:
            message.reply_text("Uh? You Reporting A Disaster...lol")
            return

        else:pass

        if chat.username and chat.type == Chat.SUPERGROUP:

            reported = f"{mention_html(user.id, user.first_name)} Reported {mention_html(reported_user.id, reported_user.first_name)} To The Admin!"

            msg = (
                f"<b>⚠️ Report: </b>{html.escape(chat.title)}\n"
                f"<b> ❍ Reported By:</b> {mention_html(user.id, user.first_name)}(<code>{user.id}</code>)\n"
                f"<b> ❍ Reported User:</b> {mention_html(reported_user.id, reported_user.first_name)} (<code>{reported_user.id}</code>)\n"
            )
            link = f'<b> ❍ Reported Message:</b> <a href="https://t.me/{chat.username}/{message.reply_to_message.message_id}">Click Here</a>'
            should_forward = False
            keyboard = [
                [
                    InlineKeyboardButton(
                        "➡ Message",
                        url=f"https://t.me/{chat.username}/{message.reply_to_message.message_id}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        " Kick ",
                        callback_data=f"report_{chat.id}=kick={reported_user.id}={reported_user.first_name}",
                    ),
                    InlineKeyboardButton(
                        " Ban ",
                        callback_data=f"report_{chat.id}=banned={reported_user.id}={reported_user.first_name}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        " Delete Message ",
                        callback_data=f"report_{chat.id}=delete={reported_user.id}={message.reply_to_message.message_id}",
                    ),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            reported = (
                f"{mention_html(user.id, user.first_name)} Reported "
                f"{mention_html(reported_user.id, reported_user.first_name)} To The Admins!"
            )

            msg = f'{mention_html(user.id, user.first_name)} Is Calling For Admins In "{html.escape(chat_name)}" !'
            link = ""
            should_forward = True

        for admin in admin_list:
            if admin.user.is_bot:  # can't message bots
                continue

            if sql.user_should_report(admin.user.id):
                try:
                    if chat.type != Chat.SUPERGROUP:
                        bot.send_message(
                            admin.user.id, msg + link, parse_mode=ParseMode.HTML,
                        )

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if (
                                len(message.text.split()) > 1
                            ):  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)
                    if not chat.username:
                        bot.send_message(
                            admin.user.id, msg + link, parse_mode=ParseMode.HTML,
                        )

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if (
                                len(message.text.split()) > 1
                            ):  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)

                    if chat.username and chat.type == Chat.SUPERGROUP:
                        bot.send_message(
                            admin.user.id,
                            msg + link,
                            parse_mode=ParseMode.HTML,
                            reply_markup=reply_markup,
                        )

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if (
                                len(message.text.split()) > 1
                            ):  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)

                except Unauthorized:
                    pass
                except BadRequest as excp:  # TODO: cleanup exceptions
                    LOGGER.exception("Exception while reporting user")

        message.reply_to_message.reply_text(
            f"{mention_html(user.id, user.first_name)} Reported The Message To The Admins! .",
            parse_mode=ParseMode.HTML,
        )
        return msg

    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, _):
    return f"This Chat Is Setup To Send User Reports To Admins, VIA  /report Or @admin: `{sql.chat_should_report(chat_id)}` "


def __user_settings__(user_id):
    return (
        "You Will Receive Reports From Chat You're Admin."
        if sql.user_should_report(user_id) is True
        else "You Will *Not* Receive Reports From Chats You're Admin!"
    )


def buttons(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    splitter = query.data.replace("report_", "").split("=")
    if splitter[1] == "kick":
        try:
            bot.kickChatMember(splitter[0], splitter[2])
            bot.unbanChatMember(splitter[0], splitter[2])
            query.answer("Successfully Kicked")
            return ""
        except Exception as err:
            query.answer(" Failed To Kick")
            bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML,
            )
    elif splitter[1] == "banned":
        try:
            bot.kickChatMember(splitter[0], splitter[2])
            query.answer(" Successfully Banned")
            return ""
        except Exception as err:
            bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML,
            )
            query.answer(" Failed To Ban")
    elif splitter[1] == "delete":
        try:
            bot.deleteMessage(splitter[0], splitter[3])
            query.answer("Message Deleted")
            return ""
        except Exception as err:
            bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML,
            )
            query.answer("Failed To Delete Message!")


__help__ = """
  » `/report <reason>`*:* Reply To A Message To Report It To Admins.
 » `@admins`*:* Reply To A message To Report It To Admins.
*Note:* Neither Or These Will Get Triggered If Used By Admins.

*Admins only:*
  » `/reports` <on/off>*:* Change Report Setting, Or View Current Status.
   » If Done In Pm, Toggles Your Status..
   » f In Group, Toggles That Groups Status.
"""

SETTING_HANDLER = CommandHandler("reports", report_setting, run_async=True)
REPORT_HANDLER = CommandHandler("report", report, filters=Filters.chat_type.groups, run_async=True)
ADMIN_REPORT_HANDLER = MessageHandler(Filters.regex(r"(?i)@admins(s)?"), report, run_async=True)
REPORT_BUTTON_USER_HANDLER = CallbackQueryHandler(buttons, pattern=r"report_")
REPORT_HANDLER2 = MessageHandler(Filters.regex(r"(?i)@lomda(s)?"), report, run_async=True)

dispatcher.add_handler(REPORT_BUTTON_USER_HANDLER)
dispatcher.add_handler(SETTING_HANDLER)
dispatcher.add_handler(REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(ADMIN_REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(REPORT_HANDLER2, REPORT_GROUP)

__mod_name__ = "Reporting"
__handlers__ = [
    (REPORT_HANDLER, REPORT_GROUP),
    (ADMIN_REPORT_HANDLER, REPORT_GROUP),
    (SETTING_HANDLER),
]
