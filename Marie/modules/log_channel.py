from datetime import datetime
from functools import wraps
from telegram.ext import CallbackContext
from Marie.modules.helper_funcs.misc import is_module_loaded

FILENAME = __name__.rsplit(".", 1)[-1]

if is_module_loaded(FILENAME):
    from telegram import ParseMode, Update
    from telegram.error import BadRequest, Unauthorized
    from telegram.ext import CommandHandler, JobQueue, run_async
    from telegram.utils.helpers import escape_markdown

    from Marie import EVENT_LOGS, LOGGER, dispatcher
    from Marie.modules.helper_funcs.chat_status import user_admin
    from Marie.modules.sql import log_channel_sql as sql

    def loggable(func):
        @wraps(func)
        def log_action(
            update: Update,
            context: CallbackContext,
            job_queue: JobQueue = None,
            *args,
            **kwargs,
        ):
            if not job_queue:
                result = func(update, context, *args, **kwargs)
            else:
                result = func(update, context, job_queue, *args, **kwargs)

            chat = update.effective_chat
            message = update.effective_message

            if result:
                datetime_fmt = "%H:%M - %d-%m-%Y"
                result += f"\n<b>Event Stamp</b>: <code>{datetime.utcnow().strftime(datetime_fmt)}</code>"

                if message.chat.type == chat.SUPERGROUP and message.chat.username:
                    result += f'\n<b>Link:</b> <a href="https://t.me/{chat.username}/{message.message_id}">click here</a>'
                log_chat = sql.get_chat_log_channel(chat.id)
                if log_chat:
                    send_log(context, log_chat, chat.id, result)

            return result

        return log_action

    def gloggable(func):
        @wraps(func)
        def glog_action(update: Update, context: CallbackContext, *args, **kwargs):
            result = func(update, context, *args, **kwargs)
            chat = update.effective_chat
            message = update.effective_message

            if result:
                datetime_fmt = "%H:%M - %d-%m-%Y"
                result += "\n<b>Event Stamp</b>: <code>{}</code>".format(
                    datetime.utcnow().strftime(datetime_fmt)
                )

                if message.chat.type == chat.SUPERGROUP and message.chat.username:
                    result += f'\n<b>Link:</b> <a href="https://t.me/{chat.username}/{message.message_id}">click here</a>'
                log_chat = str(EVENT_LOGS)
                if log_chat:
                    send_log(context, log_chat, chat.id, result)

            return result

        return glog_action

    def send_log(
        context: CallbackContext, log_chat_id: str, orig_chat_id: str, result: str
    ):
        bot = context.bot
        try:
            bot.send_message(
                log_chat_id,
                result,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except BadRequest as excp:
            if excp.message == "Chat not found":
                bot.send_message(
                    orig_chat_id, "This Log Channel Has Been Deleted - Unsetting."
                )
                sql.stop_chat_logging(orig_chat_id)
            else:
                LOGGER.warning(excp.message)
                LOGGER.warning(result)
                LOGGER.exception("Could not parse")

                bot.send_message(
                    log_chat_id,
                    result
                    + "\n\nFormatting Has Been Disabled Due To An Unexpected Error.",
                )

    @user_admin
    def logging(update: Update, context: CallbackContext):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat

        log_channel = sql.get_chat_log_channel(chat.id)
        if log_channel:
            log_channel_info = bot.get_chat(log_channel)
            message.reply_text(
                f"This Group Has All Its Logs Sent To :"
                f" {escape_markdown(log_channel_info.title)} (`{log_channel}`)",
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            message.reply_text("No Log Channel Has Been Set For This Group!")

    @user_admin
    def setlog(update: Update, context: CallbackContext):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat
        if chat.type == chat.CHANNEL:
            message.reply_text(
                "Now, Forward The /setlog To The Group You Want To Tie This Channel To!"
            )

        elif message.forward_from_chat:
            sql.set_chat_log_channel(chat.id, message.forward_from_chat.id)
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message == "Message to delete not found":
                    pass
                else:
                    LOGGER.exception(
                        "ERROR deleting message in log channel. should work anyway though."
                    )

            try:
                bot.send_message(
                    message.forward_from_chat.id,
                    f"This Channel Has Been Set As The Log Channel For {chat.title or chat.first_name}.",
                )
            except Unauthorized as excp:
                if excp.message == "Forbidden: bot is not a member of the channel chat":
                    bot.send_message(chat.id, "Successfully Set Log Channel!")
                else:
                    LOGGER.exception("ERROR in setting the log channel.")

            bot.send_message(chat.id, "Successfully Set Log Channel!")

        else:
            message.reply_text(

            "The Steps To Set Log Channel Are:\n"
            " - Add Bot To The Desired Channel\n" 
            " - Send /setlog To The Channel\n"
            " - Forward The /setlog To The Group\n"
            )

    @user_admin
    def unsetlog(update: Update, context: CallbackContext):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat

        log_channel = sql.stop_chat_logging(chat.id)
        if log_channel:
            bot.send_message(
                log_channel, f"Channel Has Been Unlinked From {chat.title} ."
            )
            message.reply_text("Log Channel Has Been Un-Set.")

        else:
            message.reply_text("No Log Channel Has Been Set Yet !")

    def __stats__():
        return f"× {sql.num_logchannels()} Log Channels Set."

    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)

    def __chat_settings__(chat_id, user_id):
        log_channel = sql.get_chat_log_channel(chat_id)
        if log_channel:
            log_channel_info = dispatcher.bot.get_chat(log_channel)
            return f"This Group Has All Its Logs Sent To: {escape_markdown(log_channel_info.title)} (`{log_channel}`) ."
        return "No Log Channel Is Set For This Group!"


    __help__ = """
» `/logchannel`*:* Get Log Channel Info 
» `/setlog`*:* Set The Log Channel.
» `/unsetlog`*:* Unset The Log Channel.

*Setting The Log Channel Is Done BY*:

» Adding The Bot To The Desired Channel (As An Admin!)
» Sending `/setlog` In The Channel 
» Forwarding The `/setlog` To The Group 

"""

    __mod_name__ = "Log-Channel"

    LOG_HANDLER = CommandHandler("logchannel", logging, run_async=True)
    SET_LOG_HANDLER = CommandHandler("setlog", setlog, run_async=True)
    UNSET_LOG_HANDLER = CommandHandler("unsetlog", unsetlog, run_async=True)

    dispatcher.add_handler(LOG_HANDLER)
    dispatcher.add_handler(SET_LOG_HANDLER)
    dispatcher.add_handler(UNSET_LOG_HANDLER)

else:
    # run anyway if module not loaded
    def loggable(func):
        return func

    def gloggable(func):
        return func
