from typing import List

from telegram import Update, Bot, Chat, Message, User
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from tg_bot.modules.helper_funcs.chat_status import bot_admin
from tg_bot.modules.helper_funcs.filters import CustomFilters

from tg_bot import dispatcher

@run_async
@bot_admin
def getlink(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = int(args[0])
    else:
        update.effective_message.reply_text("You don't seem to be referring to a chat")
    chat = bot.get_chat(chat_id)
    bot_member = chat.get_member(bot.id)
    if bot_member.can_invite_users:
        invitelink = bot.exportChatInviteLink(chat_id)
        update.effective_message.reply_text(invitelink)
    else:
        update.effective_message.reply_text("I don't have access to the invite link!")

GETLINK_HANDLER = CommandHandler("getlink", getlink, pass_args=True, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(GETLINK_HANDLER)