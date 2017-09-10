from telegram.ext import CommandHandler
from telegram.ext.dispatcher import run_async

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs import bot_admin, user_admin
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
    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id

    else:
        message.reply_text("You'll need to either give me a username to mute, or reply to someone to be muted.")
        return

    if user_id == bot.id:
        message.reply_text("I'm not muting myself!")
        return

    member = chat.get_member(int(user_id))
    print(member)

    if member:
        if member.status == 'administrator' or member.status == 'creator':
            message.reply_text("Afraid I can't stop an admin from talking!")
            return

        success = bot.restrict_chat_member(chat.id, user_id, can_send_messages=False)

        if success:
            message.reply_text("Muted!")
        else:
            message.reply_text("Did not go as expected - couldn't mute this user!")


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
    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id

    else:
        message.reply_text("You'll need to either give me a username to mute, or reply to someone to be muted.")
        return

    success = bot.restrict_chat_member(chat.id, int(user_id),
                                       can_send_messages=True,
                                       can_send_media_messages=True,
                                       can_send_other_messages=True,
                                       can_add_web_page_previews=True)
    if success:
        message.reply_text("Unmuted!")

    else:
        message.reply_text("Uh... I couldn't unmute this one")


__help__ = """
 - /mute: silences a user
 - /unmute <userhandle>: unmutes a user
"""

MUTE_HANDLER = CommandHandler("mute", mute, pass_args=True)
UNMUTE_HANDLER = CommandHandler("unmute", unmute, pass_args=True)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
