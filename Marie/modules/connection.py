import time
import re

from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, Update, Bot
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler, CallbackQueryHandler

import Marie.modules.sql.connection_sql as sql
from Marie import dispatcher, DRAGONS, DEV_USERS
from Marie.modules.helper_funcs import chat_status
from Marie.modules.helper_funcs.alternate import send_message, typing_action

user_admin = chat_status.user_admin


@user_admin
@typing_action
def allow_connections(update, context) -> str:

    chat = update.effective_chat
    args = context.args

    if chat.type != chat.PRIVATE:
        if len(args) >= 1:
            var = args[0]
            if var == "no":
                sql.set_allow_connect_to_chat(chat.id, False)
                send_message(
                    update.effective_message,
                    "Connection Has Been Disabled For This Chat",
                )
            elif var == "yes":
                sql.set_allow_connect_to_chat(chat.id, True)
                send_message(
                    update.effective_message,
                    "Connection Has Been Enabled For This Chat",
                )
            else:
                send_message(
                    update.effective_message,
                    "Please Enter `yes` or `no` Okay!",
                    parse_mode=ParseMode.MARKDOWN,
                )
        else:
            get_settings = sql.allow_connect_to_chat(chat.id)
            if get_settings:
                send_message(
                    update.effective_message,
                    "Connection To This Group Are *ALLOWED* for Members!",
                    parse_mode=ParseMode.MARKDOWN,
                )
            else:
                send_message(
                    update.effective_message,
                    "Connection To This Group Are *NOT ALLOWED* for Members!",
                    parse_mode=ParseMode.MARKDOWN,
                )
    else:
        send_message(
            update.effective_message,
            "This Command Is For Group Only Not In PM!",
        )


@typing_action
def connection_chat(update, context):

    chat = update.effective_chat
    user = update.effective_user

    conn = connected(context.bot, update, chat, user.id, need_admin=True)

    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type != "private":
            return
        chat = update.effective_chat
        chat_name = update.effective_message.chat.title

    if conn:
        message = "You Are Currently Connected To {} okay.\n".format(chat_name)
    else:
        message = "You Are Currently Not Connected In Any Group.\n"
    send_message(update.effective_message, message, parse_mode="markdown")


@typing_action
def connect_chat(update, context):

    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if update.effective_chat.type == "private":
        if args and len(args) >= 1:
            try:
                connect_chat = int(args[0])
                getstatusadmin = context.bot.get_chat_member(
                    connect_chat,
                    update.effective_message.from_user.id,
                )
            except ValueError:
                try:
                    connect_chat = str(args[0])
                    get_chat = context.bot.getChat(connect_chat)
                    connect_chat = get_chat.id
                    getstatusadmin = context.bot.get_chat_member(
                        connect_chat,
                        update.effective_message.from_user.id,
                    )
                except BadRequest:
                    send_message(update.effective_message, "Invalid Chat ID!")
                    return
            except BadRequest:
                send_message(update.effective_message, "Invalid Chat ID!")
                return

            isadmin = getstatusadmin.status in ("administrator", "creator")
            ismember = getstatusadmin.status in ("member")
            isallow = sql.allow_connect_to_chat(connect_chat)

            if (isadmin) or (isallow and ismember) or (user.id in DRAGONS):
                connection_status = sql.connect(
                    update.effective_message.from_user.id,
                    connect_chat,
                )
                if connection_status:
                    conn_chat = dispatcher.bot.getChat(
                        connected(context.bot, update, chat, user.id, need_admin=False),
                    )
                    chat_name = conn_chat.title
                    send_message(
                        update.effective_message,
                        "Successfully Connected To *{}*. \nᴜꜱᴇ /helpconnect  To Check Available Commands.".format(
                            chat_name,
                        ),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    sql.add_history_conn(user.id, str(conn_chat.id), chat_name)
                else:
                    send_message(update.effective_message, "Connection failed!")
            else:
                send_message(
                    update.effective_message,
                    "Connected To This Chat Is Not Allowed!",
                )
        else:
            gethistory = sql.get_history_conn(user.id)
            if gethistory:
                buttons = [
                    InlineKeyboardButton(
                        text=" Close button",
                        callback_data="connect_close",
                    ),
                    InlineKeyboardButton(
                        text=" Clear history",
                        callback_data="connect_clear",
                    ),
                ]
            else:
                buttons = []
            conn = connected(context.bot, update, chat, user.id, need_admin=False)
            if conn:
                connectedchat = dispatcher.bot.getChat(conn)
                text = "You Are Currently Connected To *{}* (`{}`) ..".format(
                    connectedchat.title,
                    conn,
                )
                buttons.append(
                    InlineKeyboardButton(
                        text="🔌 Disconnect",
                        callback_data="connect_disconnect",
                    ),
                )
            else:
                text = "Write The Chat ID Or Tag To Connect!"
            if gethistory:
                text += "\n\n*Connection History:*\n"
                text += "「 *Info* 」\n"
                text += " Sorted: `Newest`\n"
                text += "│\n"
                buttons = [buttons]
                for x in sorted(gethistory.keys(), reverse=True):
                    htime = time.strftime("%d/%m/%Y", time.localtime(x))
                    text += "╞═「 *{}* 」\n│   `{}`\n│   `{}`\n".format(
                        gethistory[x]["chat_name"],
                        gethistory[x]["chat_id"],
                        htime,
                    )
                    text += "│\n"
                    buttons.append(
                        [
                            InlineKeyboardButton(
                                text=gethistory[x]["chat_name"],
                                callback_data="connect({})".format(
                                    gethistory[x]["chat_id"],
                                ),
                            ),
                        ],
                    )
                text += "「 Total {} Chats 」".format(
                    str(len(gethistory)) + " (max)"
                    if len(gethistory) == 5
                    else str(len(gethistory)),
                )
                conn_hist = InlineKeyboardMarkup(buttons)
            elif buttons:
                conn_hist = InlineKeyboardMarkup([buttons])
            else:
                conn_hist = None
            send_message(
                update.effective_message,
                text,
                parse_mode="markdown",
                reply_markup=conn_hist,
            )

    else:
        getstatusadmin = context.bot.get_chat_member(
            chat.id,
            update.effective_message.from_user.id,
        )
        isadmin = getstatusadmin.status in ("administrator", "creator")
        ismember = getstatusadmin.status in ("member")
        isallow = sql.allow_connect_to_chat(chat.id)
        if (isadmin) or (isallow and ismember) or (user.id in DRAGONS):
            connection_status = sql.connect(
                update.effective_message.from_user.id,
                chat.id,
            )
            if connection_status:
                chat_name = dispatcher.bot.getChat(chat.id).title
                send_message(
                    update.effective_message,
                    "Successfully Connected To *{}* ...".format(chat_name),
                    parse_mode=ParseMode.MARKDOWN,
                )
                try:
                    sql.add_history_conn(user.id, str(chat.id), chat_name)
                    context.bot.send_message(
                        update.effective_message.from_user.id,
                        "You Are Connected To *{}*. \nUse `/helpconnect` To Check Available Commands.".format(
                            chat_name,
                        ),
                        parse_mode="markdown",
                    )
                except BadRequest:
                    pass
                except Unauthorized:
                    pass
            else:
                send_message(update.effective_message, "Connection Failed!")
        else:
            send_message(
                update.effective_message,
                "Connection To This Chat Is Not Allowed!",
            )


def disconnect_chat(update, context):

    if update.effective_chat.type == "private":
        disconnection_status = sql.disconnect(update.effective_message.from_user.id)
        if disconnection_status:
            sql.disconnected_chat = send_message(
                update.effective_message,
                "Disconnected From Chat!",
            )
        else:
            send_message(update.effective_message, "You're Not Connected!")
    else:
        send_message(update.effective_message, "This Command Is Only Available In Me PM.")


def connected(bot: Bot, update: Update, chat, user_id, need_admin=True):
    user = update.effective_user

    if chat.type == chat.PRIVATE and sql.get_connected_chat(user_id):

        conn_id = sql.get_connected_chat(user_id).chat_id
        getstatusadmin = bot.get_chat_member(
            conn_id,
            update.effective_message.from_user.id,
        )
        isadmin = getstatusadmin.status in ("administrator", "creator")
        ismember = getstatusadmin.status in ("member")
        isallow = sql.allow_connect_to_chat(conn_id)

        if (
            (isadmin)
            or (isallow and ismember)
            or (user.id in DRAGONS)
            or (user.id in DEV_USERS)
        ):
            if need_admin is True:
                if (
                    getstatusadmin.status in ("administrator", "creator")
                    or user_id in DRAGONS
                    or user.id in DEV_USERS
                ):
                    return conn_id
                send_message(
                    update.effective_message,
                    "You Must Be An Admin In The Connected Group!",
                )
            else:
                return conn_id
        else:
            send_message(
                update.effective_message,
                "The Group Changed The Connection Rights Or You Are No Longer An Admin.\nI've Disconnected You.",
            )
            disconnect_chat(update, bot)
    else:
        return False


CONN_HELP = """
 Actions are available with connected groups:
 » View and edit Notes.
 » View and edit Filters.
 » Get invite link of chat.
 » Set and control AntiFlood settings.
 » Set and control Blacklist settings.
 » Set Locks and Unlocks in chat.
 » Enable and Disable commands in chat.
 » Export and Imports of chat backup.
 » More in future!"""


def help_connect_chat(update, context):

    args = context.args

    if update.effective_message.chat.type != "private":
        send_message(update.effective_message, "Pm Me With That Command To Get Help.")
        return
    send_message(update.effective_message, CONN_HELP, parse_mode="markdown")


def connect_button(update, context):

    query = update.callback_query
    chat = update.effective_chat
    user = update.effective_user

    connect_match = re.match(r"connect\((.+?)\)", query.data)
    disconnect_match = query.data == "connect_disconnect"
    clear_match = query.data == "connect_clear"
    connect_close = query.data == "connect_close"

    if connect_match:
        target_chat = connect_match.group(1)
        getstatusadmin = context.bot.get_chat_member(target_chat, query.from_user.id)
        isadmin = getstatusadmin.status in ("administrator", "creator")
        ismember = getstatusadmin.status in ("member")
        isallow = sql.allow_connect_to_chat(target_chat)

        if (isadmin) or (isallow and ismember) or (user.id in DRAGONS):
            connection_status = sql.connect(query.from_user.id, target_chat)

            if connection_status:
                conn_chat = dispatcher.bot.getChat(
                    connected(context.bot, update, chat, user.id, need_admin=False),
                )
                chat_name = conn_chat.title
                query.message.edit_text(
                    "Successfully Connected To *{}*. \nUse `/helpconnect` To Check Available Commands.".format(
                        chat_name,
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )
                sql.add_history_conn(user.id, str(conn_chat.id), chat_name)
            else:
                query.message.edit_text("Connection failed!")
        else:
            context.bot.answer_callback_query(
                query.id,
                "Connection To This Chat Is Not Allowed!",
                show_alert=True,
            )
    elif disconnect_match:
        disconnection_status = sql.disconnect(query.from_user.id)
        if disconnection_status:
            sql.disconnected_chat = query.message.edit_text("Disconnected From Chat!")
        else:
            context.bot.answer_callback_query(
                query.id,
                "You're Not Connected!",
                show_alert=True,
            )
    elif clear_match:
        sql.clear_history_conn(query.from_user.id)
        query.message.edit_text("History Connected Has Been Cleared!")
    elif connect_close:
        query.message.edit_text("Closed.\nTo Open Again, Type /connect .")
    else:
        connect_chat(update, context)


__mod_name__ = "Connection"

__help__ = """
Sometimes, You Just Want To Add Some Notes And Filters To A Group Chat, But You Don't Want Everyone To See; This Is Where Connections Come In...
This Allows You To Connect To A Chat's Database, And Add Things To It Without The Commands Appearing In Chat! For Obvious Reasons, You Need To Be An Admin To Add Things; But Any Member In The Group Can View Your Data.

» `/connect`: Connects To Chat (Can Be Done In A Group By `/connect` Or `/connect` <chat id> In PM)
» `/connection`: List Connected Chats
» `/disconnect`: Disconnect From A Chat
» `/helpconnect`: List Available Commands That Can Be Used Remotely

*Admins Only*

» `/allowconnect` <yes/no>: Allow A User To Connect To A Chat 
"""

CONNECT_CHAT_HANDLER = CommandHandler(
    "connect", connect_chat, pass_args=True, run_async=True
)
CONNECTION_CHAT_HANDLER = CommandHandler("connection", connection_chat, run_async=True)
DISCONNECT_CHAT_HANDLER = CommandHandler("disconnect", disconnect_chat, run_async=True)
ALLOW_CONNECTIONS_HANDLER = CommandHandler(
    "allowconnect",
    allow_connections,
    pass_args=True,
    run_async=True,
)
HELP_CONNECT_CHAT_HANDLER = CommandHandler(
    "helpconnect", help_connect_chat, run_async=True
)
CONNECT_BTN_HANDLER = CallbackQueryHandler(
    connect_button, pattern=r"connect", run_async=True
)

dispatcher.add_handler(CONNECT_CHAT_HANDLER)
dispatcher.add_handler(CONNECTION_CHAT_HANDLER)
dispatcher.add_handler(DISCONNECT_CHAT_HANDLER)
dispatcher.add_handler(ALLOW_CONNECTIONS_HANDLER)
dispatcher.add_handler(HELP_CONNECT_CHAT_HANDLER)
dispatcher.add_handler(CONNECT_BTN_HANDLER)
