from telegram import MessageEntity
from telegram.ext import run_async, CommandHandler

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs import bot_admin, user_admin, is_user_admin, is_user_in_chat
from tg_bot.modules.users import get_user_id


def extract_user(message, args):
    prev_message = message.reply_to_message

    if message.entities and message.parse_entities([MessageEntity.TEXT_MENTION]):
        entities = message.parse_entities([MessageEntity.TEXT_MENTION])
        for e in entities:
            return e.user.id

    elif len(args) >= 1 and args[0][0] == '@':
        user = args[0]
        user_id = get_user_id(user)
        if not user_id:
            message.reply_text("I don't have that user in my db. You'll be able to interact with them if "
                               "you reply to that person's message instead.")
            return None
        else:
            return user_id

    elif len(args) >= 1 and args[0].isdigit():
        return int(args[0])

    elif prev_message:
        return prev_message.from_user.id

    else:
        message.reply_text("You don't seem to be referring to a user.")
        return None


@run_async
@bot_admin
@user_admin
def ban(bot, update, args):
    chat = update.effective_chat
    message = update.effective_message

    user_id = extract_user(message, args)
    if not user_id:
        return

    if is_user_admin(chat, user_id):
        message.reply_text("I really wish I could ban admins...")
        return

    res = update.effective_chat.kick_member(user_id)
    if res:
        bot.send_sticker(update.effective_chat.id, 'CAADAgADOwADPPEcAXkko5EB3YGYAg')  # banhammer marie sticker
        message.reply_text("Banned!")
    else:
        message.reply_text("Well damn, I can't ban that user.")


@run_async
@bot_admin
@user_admin
def kick(bot, update, args):
    chat = update.effective_chat
    message = update.effective_message

    user_id = extract_user(message, args)
    if not user_id:
        return

    if is_user_admin(chat, user_id):
        message.reply_text("I really wish I could ban admins...")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        bot.send_sticker(update.effective_chat.id, 'CAADAgADOwADPPEcAXkko5EB3YGYAg')  # banhammer marie sticker
        message.reply_text("Banned!")
    else:
        message.reply_text("Well damn, I can't ban that user.")


@run_async
@bot_admin
def kickme(bot, update):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("I wish I could... but you're an admin.")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("No problem.")
    else:
        update.effective_message.reply_text("Huh? I can't :/")


@run_async
@bot_admin
@user_admin
def unban(bot, update, args):
    message = update.effective_message
    chat = update.effective_chat

    user_id = extract_user(message, args)
    if not user_id:
        return

    if is_user_in_chat(chat, user_id):
        update.effective_message.reply_text("This person is already in the chat!")
        return

    res = update.effective_chat.unban_member(user_id)
    if res:
        message.reply_text("Yep, this user can join!")
    else:
        message.reply_text("Hm, couldn't unban this person.")


__help__ = """
 - /ban <userhandle>: bans a user. (via handle, or reply)
 - /unban <userhandle>: unbans a user. (via handle, or reply)
 - /kick <userhandle>: kicks a user, (via handle, or reply)
 - /kickme: kicks the user who issued the command
 """

BAN_HANDLER = CommandHandler("ban", ban, pass_args=True)
KICK_HANDLER = CommandHandler("kick", kick, pass_args=True)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True)
KICKME_HANDLER = CommandHandler("kickme", kickme)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
