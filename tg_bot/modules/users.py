import html
from io import BytesIO
from time import sleep
from typing import Optional, List

from telegram import TelegramError, Chat, Message
from telegram import Update, Bot, ParseMode
from telegram.utils.helpers import mention_html
from telegram.error import BadRequest, Unauthorized
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram.ext.dispatcher import run_async

import tg_bot.modules.sql.users_sql as sql
from tg_bot.modules.helper_funcs.misc import send_to_list
from tg_bot import dispatcher, OWNER_ID, LOGGER, SUDO_USERS
from tg_bot.modules.helper_funcs.filters import CustomFilters

USERS_GROUP = 4
CHAT_BAN_GROUP = 12


def get_user_id(username):
    # ensure valid userid
    if len(username) <= 5:
        return None

    if username.startswith('@'):
        username = username[1:]

    users = sql.get_userid_by_name(username)

    if not users:
        return None

    elif len(users) == 1:
        return users[0].user_id

    else:
        for user_obj in users:
            try:
                userdat = dispatcher.bot.get_chat(user_obj.user_id)
                if userdat.username == username:
                    return userdat.id

            except BadRequest as excp:
                if excp.message == 'Chat not found':
                    pass
                else:
                    LOGGER.exception("Error extracting user ID")

    return None


@run_async
def broadcast(bot: Bot, update: Update):
    to_send = update.effective_message.text.split(None, 1)
    if len(to_send) >= 2:
        chats = sql.get_all_chats() or []
        failed = 0
        for chat in chats:
            try:
                bot.sendMessage(int(chat.chat_id), to_send[1])
                sleep(0.1)
            except TelegramError:
                failed += 1
                LOGGER.warning("Couldn't send broadcast to %s, group name %s", str(chat.chat_id), str(chat.chat_name))

        update.effective_message.reply_text("Broadcast complete. {} groups failed to receive the message, probably "
                                            "due to being kicked.".format(failed))


@run_async
def restrict_group(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]

    # Check if there is only one argument
    if not len(args) == 1:
        message.reply_text("Incorrect number of arguments. Please use `/restrict chat_id`.",
                           parse_mode=ParseMode.MARKDOWN)
        return

    chat_id = args[0]

    # Check if chat_id is valid
    if not chat_id.startswith('-') or chat_id.isdigit():
        message.reply_text("Invalid chat id! "
                           "Ensure that the chat id is an integer and you included the '-' sign in the chat id.")
        return

    # Check if chat_id is in bot database
    chat_title = sql.get_chatname_by_chatid(chat_id)
    if chat_title is None:
        message.reply_text("I can't seem to find the chat in my database. "
                           "Use /chatlist to obtain a list of chats in my database.")
        return

    chat_restricted = sql.get_restriction(chat_id)
    if not chat_restricted:
        chat_title = html.escape(chat_title)

        sudo_users_list = "<b>My Admins:</b>"
        for user in SUDO_USERS:
            name = mention_html(user, bot.get_chat(user).first_name)
            sudo_users_list += "\n - {}".format(name)
        
        try:
            bot.send_message(chat_id=chat_id,
                             text="I have been restricted by my admins from this chat. "
                                  "Request any of my admins to add me to this chat.\n\n"
                                  "{}".format(sudo_users_list), parse_mode=ParseMode.HTML)
        except Unauthorized as excp:
            if excp.message == "Forbidden: bot is not a member of the supergroup chat":
                message.reply_text("Looks like I'm no longer a part of that chat!")
                return
            else:
                LOGGER.exception("Error while sending message to chat.")
        
        bot.leave_chat(chat_id)

        sql.set_restriction(chat_id, chat_title, restricted=True)
        
        message.reply_text("Successfully left chat <b>{}</b>!".format(chat_title), parse_mode=ParseMode.HTML)
            
        # Report to sudo users
        restrictor = update.effective_user  # type: Optional[User]
        send_to_list(bot, SUDO_USERS, "{} has restricted me from being added to the chat <b>{}</b>."
                     .format(mention_html(restrictor.id, restrictor.first_name), chat_title), html=True)
                    
    else:
        message.reply_text("I'm already restricted from that chat!")
                

@run_async
def new_message(bot: Bot, update: Update):  # Leave group when a message is sent in restricted group
    chat = update.effective_chat  # type: Optional[Chat]

    bot.send_message(chat_id=chat.id,
                     text="I have been restricted by my admins from this chat! "
                          "Request any of my admins to add me to this chat.")
    bot.leave_chat(chat.id)


@run_async
def unrestrict_group(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    
    # Check if there is only one argument
    if not len(args) == 1:
        message.reply_text("Incorrect number of arguments. Please use `/unrestrict chat_id`.",
                           parse_mode=ParseMode.MARKDOWN)
        return

    chat_id = args[0]

    # Check if chat_id is valid
    if not chat_id.startswith('-') or chat_id.isdigit():
        message.reply_text("Invalid chat id! "
                           "Ensure that the chat id is an integer and you included the '-' sign in the chat id.")
        return

    # Check if chat_id is in bot database
    chat_title = sql.get_chatname_by_chatid(chat_id)
    if chat_title is None:
        message.reply_text("I can't seem to find the chat in my database. "
                           "Use /chatlist to obtain a list of chats in my database.")
        return
    
    chat_restricted = sql.get_restriction(chat_id)            
    if chat_restricted:
        chat_title = html.escape(chat_title)
        sql.set_restriction(chat_id, chat_title, restricted=False)
        
        message.reply_text("Successfully removed all restrictions on the chat <b>{}</b>!"
                           .format(chat_title), parse_mode=ParseMode.HTML)
                
        # Report to sudo users
        unrestrictor = update.effective_user  # type: Optional[User]
        send_to_list(bot, SUDO_USERS, "{} has removed my restrictions on the chat <b>{}</b>."
                     .format(mention_html(unrestrictor.id, unrestrictor.first_name), chat_title), html=True)
            
    else:
        message.reply_text("I'm not restricted from that chat!")


@run_async
def log_user(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    sql.update_user(msg.from_user.id,
                    msg.from_user.username,
                    chat.id,
                    chat.title)

    if msg.reply_to_message:
        sql.update_user(msg.reply_to_message.from_user.id,
                        msg.reply_to_message.from_user.username,
                        chat.id,
                        chat.title)

    if msg.forward_from:
        sql.update_user(msg.forward_from.id,
                        msg.forward_from.username)


@run_async
def chats(bot: Bot, update: Update):
    all_chats = sql.get_all_chats() or []
    chatfile = 'List of chats.\n'
    for chat in all_chats:
        chat_restricted = sql.get_restriction(chat.chat_id)

        if chat_restricted:
            chatfile += "{} - ({}) [R]\n".format(chat.chat_name, chat.chat_id)
        else:
            chatfile += "{} - ({})\n".format(chat.chat_name, chat.chat_id)

    if any(chat.restricted == True for chat in all_chats):
        chatfile += "[R] - Restricted chat"

    with BytesIO(str.encode(chatfile)) as output:
        output.name = "chatlist.txt"
        update.effective_message.reply_document(document=output, filename="chatlist.txt",
                                                caption="Here is the list of chats in my database.")


def __user_info__(user_id):
    if user_id == dispatcher.bot.id:
        return """I've seen them in... Wow. Are they stalking me? They're in all the same places I am... oh. It's me."""
    num_chats = sql.get_user_num_chats(user_id)
    return """I've seen them in <code>{}</code> chats in total.""".format(num_chats)


def __stats__():
    return "{} users, across {} chats".format(sql.num_users(), sql.num_chats())


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = ""  # no help string

__mod_name__ = "Users"

BROADCAST_HANDLER = CommandHandler("broadcast", broadcast, filters=Filters.user(OWNER_ID))
USER_HANDLER = MessageHandler(Filters.all & Filters.group, log_user)
CHATLIST_HANDLER = CommandHandler("chatlist", chats, filters=CustomFilters.sudo_filter)
RESTRICT_GROUP_HANDLER = CommandHandler("restrict", restrict_group, pass_args=True, 
                                        filters=CustomFilters.sudo_filter)
UNRESTRICT_GROUP_HANDLER = CommandHandler("unrestrict", unrestrict_group, pass_args=True, 
                                          filters=CustomFilters.sudo_filter)
NEW_MESSAGE_HANDLER = MessageHandler(CustomFilters.chat_restricted, new_message)

dispatcher.add_handler(USER_HANDLER, USERS_GROUP)
dispatcher.add_handler(BROADCAST_HANDLER)
dispatcher.add_handler(CHATLIST_HANDLER)
dispatcher.add_handler(RESTRICT_GROUP_HANDLER)
dispatcher.add_handler(UNRESTRICT_GROUP_HANDLER)
dispatcher.add_handler(NEW_MESSAGE_HANDLER, CHAT_BAN_GROUP)
