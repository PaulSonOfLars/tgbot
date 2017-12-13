from telegram import MessageEntity
from telegram.ext import CommandHandler, run_async

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs import user_admin, bot_admin
from tg_bot.modules.sql import warns_sql as sql
from tg_bot.modules.users import get_user_id


# TODO: Make a single user_id and argument extraction function! this one is inaccurate
def extract_userid(message):
    args = message.text.split(None, 2)  # use python's maxsplit to separate Cmd, warn recipient, and warn reason

    if len(args) >= 2 and args[1][0] == '@':
        user = args[1]
        user_id = get_user_id(user)
        if not user_id:
            message.reply_text("I don't have that user in my db. You'll be able to interact with them if "
                               "you reply to that person's message instead.")
            return
        return user_id, args[2]

    elif message.entities and message.parse_entities([MessageEntity.TEXT_MENTION]):
        entities = message.parse_entities([MessageEntity.TEXT_MENTION])
        for e in entities:
            return e.user.id, message.text.split(None, 1)[1]  # TODO: User entity offset here to account for split names

    elif message.reply_to_message:
        return message.reply_to_message.from_user.id, message.text.split(None, 1)[1]


@run_async
@user_admin
@bot_admin
def warn(bot, update):
    message = update.effective_message
    chat = update.effective_chat

    user_id, reason = extract_userid(message) or None, ""
    if user_id:
        user_warned = sql.warn_user(user_id, chat.id, reason)
        if user_warned.num_warns >= 3:
            # TODO: check if member is admin/creator
            res = chat.kick_member(user_id)
            if res:
                bot.send_sticker(chat.id, 'CAADAgADOwADPPEcAXkko5EB3YGYAg')  # banhammer marie sticker
                message.reply_text("3 warnings, this user has been banned!")
                sql.reset_warns(user_id, chat.id)
            else:
                message.reply_text("An error occurred, I couldn't ban this person!")
        else:
            message.reply_text("{}/3 warnings... watch out!".format(user_warned.num_warns))
    else:
        message.reply_text("No user was designated!")


@run_async
@user_admin
@bot_admin
def reset_warns(bot, update):
    message = update.effective_message
    chat = update.effective_chat

    user_id, _ = extract_userid(message) or None, None
    if user_id:
        sql.reset_warns(user_id, chat.id)
        message.reply_text("Warnings have been reset!")
    else:
        message.reply_text("No user has been designated!")


def warns(bot, update):
    message = update.effective_message
    user_id, _ = extract_userid(message) or update.effective_user.id, None
    warned_user = sql.get_warns(user_id, update.effective_chat.id)
    if warned_user and warned_user.num_warns != 0:
        if warned_user.reasons:
            text = "This user has {} warnings, for the following reasons:".format(warned_user.num_warns)
            for reason in warned_user.reasons:
                text += "\n - {}".format(reason)
            # TODO: Check length of text to send.
            update.effective_message.reply_text(text)
        else:
            update.effective_message.reply_text(
                "User has {} warnings, but no reasons for any of them.".format(warned_user.num_warns))
    else:
        update.effective_message.reply_text("This user hasn't got any warnings!")


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = """
 - /warn <userhandle>: warn a user. After 3 warns, the user will be banned from the group. Can also be used as a reply.
 - /resetwarn <userhandle>: reset the warnings for a user. Can also be used as a reply.
 - /warns <userhandle>: get a user's number, and reason, of warnings.
"""

WARN_HANDLER = CommandHandler("warn", warn)
RESET_WARN_HANDLER = CommandHandler("resetwarn", reset_warns)
MYWARNS_HANDLER = CommandHandler("warns", warns)

dispatcher.add_handler(WARN_HANDLER)
dispatcher.add_handler(RESET_WARN_HANDLER)
dispatcher.add_handler(MYWARNS_HANDLER)
