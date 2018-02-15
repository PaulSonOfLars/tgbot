from typing import Optional, List

from telegram import Message, Chat, Update, Bot
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher, BAN_STICKER, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.log_channel import loggable


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("I really wish I could ban admins...")
        return ""

    if user_id == bot.id:
        update.effective_message.reply_text("I'm not gonna BAN myself, are you crazy?")
        return ""

    try:
        update.effective_chat.kick_member(user_id)
        bot.send_sticker(update.effective_chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Banned!")
        return "{}:" \
               "\n#BANNED" \
               "\n*Admin:* [{}](tg://user?id={})" \
               "\n*User:* [{}](tg://user?id={})".format(escape_markdown(chat.title),
                                                        escape_markdown(update.effective_user.first_name),
                                                        update.effective_user.id,
                                                        escape_markdown(member.user.first_name),
                                                        member.user.id)
    except BadRequest as excp:
        message.reply_text("Well damn, I can't ban that user.")
        LOGGER.warning(update)
        LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id, excp.message)

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id):
        message.reply_text("I really wish I could kick admins...")
        return ""

    if user_id == bot.id:
        update.effective_message.reply_text("Yeahhh I'm not gonna do that")
        return ""

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        bot.send_sticker(update.effective_chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Kicked!")
        return "{}:" \
               "\n#KICKED" \
               "\n*Admin:* [{}](tg://user?id={})" \
               "\n*User:* [{}](tg://user?id={})".format(escape_markdown(chat.title),
                                                        escape_markdown(update.effective_user.first_name),
                                                        update.effective_user.id,
                                                        escape_markdown(member.user.first_name),
                                                        member.user.id)
    else:
        message.reply_text("Well damn, I can't kick that user.")

    return ""


@run_async
@bot_admin
@can_restrict
def kickme(bot: Bot, update: Update):
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
@can_restrict
@user_admin
@loggable
def unban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]

    user_id = extract_user(message, args)
    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if user_id == bot.id:
        update.effective_message.reply_text("How would I unban myself if I wasn't here...?")
        return ""

    if is_user_in_chat(chat, user_id):
        update.effective_message.reply_text("Why are you trying to unban someone that's already in the chat?")
        return ""

    update.effective_chat.unban_member(user_id)
    message.reply_text("Yep, this user can join!")

    return "{}:" \
           "\n#UNBANNED" \
           "\n*Admin:* [{}](tg://user?id={})" \
           "\n*User:* [{}](tg://user?id={})".format(escape_markdown(chat.title),
                                                    escape_markdown(update.effective_user.first_name),
                                                    update.effective_user.id,
                                                    escape_markdown(member.user.first_name),
                                                    member.user.id)


__help__ = """
 - /kickme: kicks the user who issued the command

*Admin only:*
 - /ban <userhandle>: bans a user. (via handle, or reply)
 - /unban <userhandle>: unbans a user. (via handle, or reply)
 - /kick <userhandle>: kicks a user, (via handle, or reply)
"""

__mod_name__ = "Bans"


BAN_HANDLER = CommandHandler("ban", ban, pass_args=True, filters=Filters.group)
KICK_HANDLER = CommandHandler("kick", kick, pass_args=True, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
