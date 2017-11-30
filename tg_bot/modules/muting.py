from telegram.ext import CommandHandler
from telegram.ext.dispatcher import run_async

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs import bot_admin, user_admin, is_user_admin
from tg_bot.modules.users import get_user_id


@bot_admin
@user_admin
@run_async
def mute(bot, update, args):
    chat = update.effective_chat
    message = update.effective_message

    if len(args) >= 1 and args[0][0] == '@':
        user = args[0]
        user_id = get_user_id(user)
        if not user_id:
            message.reply_text("I don't have that user in my db. You'll be able to interact with them if "
                               "you reply to that person's message instead.")
            return

    elif message.entities and message.parse_entities('text_mention'):
        entities = message.parse_entities('text_mention')
        for e in entities:
            user_id = e.user.id
            break
        else:
            return

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id

    else:
        message.reply_text("You'll need to either give me a username to mute, or reply to someone to be muted.")
        return

    if user_id == bot.id:
        message.reply_text("I'm not muting myself!")
        return

    member = chat.get_member(int(user_id))

    if member:
        if is_user_admin(chat, user_id, member=member):
            message.reply_text("Afraid I can't stop an admin from talking!")

        elif member.can_send_messages is None or member.can_send_messages:
            success = bot.restrict_chat_member(chat.id, user_id, can_send_messages=False)
            if success:
                message.reply_text("Muted!")
            else:
                message.reply_text("Did not go as expected - couldn't mute this user!")

        else:
            message.reply_text("This user is already muted!")
    else:
        message.reply_text("This user isn't in the chat!")


@bot_admin
@user_admin
@run_async
def unmute(bot, update, args):
    chat = update.effective_chat
    message = update.effective_message

    if len(args) >= 1 and args[0][0] == '@':
        user = args[0]
        user_id = get_user_id(user)
        if not user_id:
            message.reply_text("I don't have that user in my db. You'll be able to interact with them if "
                               "you reply to that person's message instead.")
            return

    elif message.entities and message.parse_entities('text_mention'):
        entities = message.parse_entities('text_mention')
        for e in entities:
            user_id = e.user.id
            break
        else:
            return

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id

    else:
        message.reply_text("You'll need to either give me a username to mute, or reply to someone to be muted.")
        return

    member = chat.get_member(int(user_id))

    if member:
        if member.can_send_messages and member.can_send_media_messages \
                and member.can_send_other_messages and member.can_add_web_page_previews:
            message.reply_text("This user already has the right to speak.")
        else:
            success = bot.restrict_chat_member(chat.id, int(user_id),
                                               can_send_messages=True,
                                               can_send_media_messages=True,
                                               can_send_other_messages=True,
                                               can_add_web_page_previews=True)
            if success:
                message.reply_text("Unmuted!")

            else:
                message.reply_text("Uh... I couldn't unmute this one")
    else:
        message.reply_text("This user isn't even in the chat, unmuting him won't help!")


__help__ = """
 - /mute <userhandle>: silences a user. Can also be used as a reply, muting the replied to user.
 - /unmute <userhandle>: unmutes a user. Can also be used as a reply, muting the replied to user.
"""

MUTE_HANDLER = CommandHandler("mute", mute, pass_args=True)
UNMUTE_HANDLER = CommandHandler("unmute", unmute, pass_args=True)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
