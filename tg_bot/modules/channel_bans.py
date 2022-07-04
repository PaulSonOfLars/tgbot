from typing import Optional, List

from telegram import Chat, Update, Bot, ParseMode
from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import user_not_admin, user_admin, bot_can_delete
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import channel_bans_sql as sql

@user_admin
@bot_can_delete
@loggable
def ban_channel(bot: Bot, update: Update, args: List[str]) -> str:
    channel_name = args[0]
    chat_id = update.effective_chat.id
    sql.add_channel_bans(chat_id, channel_name)
    return ""


@run_async
@user_admin
@loggable
def unban_channel(bot: Bot, update: Update, args: List[str]) -> str:
    channel_name = args[0]
    chat_id = update.effective_chat.id
    sql.delete_channel_ban(chat_id, channel_name)
    return ""


@run_async
# @user_not_admin
def kek(bot: Bot, update: Update):
    forwarder_from_channel_name = update.effective_message.forward_from_chat.username
    is_exists = sql.is_channel_ban_exists(update.effective_chat.id, forwarder_from_channel_name)
    if is_exists:
        update.effective_message.reply_text("Channel " + forwarder_from_channel_name + " banned")
        update.effective_message.delete()

@run_async
@user_admin
def banned_channels(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    res = sql.get_channel_bans(chat.id)
    res = map(lambda x: x.channel_to_ban, res)
    update.effective_message.reply_text(','.join(res), parse_mode=ParseMode.MARKDOWN)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)

__help__ = """
 - /banned_channels: list all banned channels in this chat.

*Admin only:*
 - /ban_channel <channel_name>: ban a channel in this chat. The bot will now delete messages forwarded from the channel mentioned.
 - /unban_channel <channel_name>: unban a channel in this chat.
"""

__mod_name__ = "Channel Bans"

BAN_CHANNEL_HANDLER = CommandHandler("ban_channel", ban_channel, pass_args=True, filters=Filters.group)
UNBAN_CHANNEL_HANDLER = CommandHandler("unban_channel", unban_channel, pass_args=True, filters=Filters.group)
BANNED_CHANNELS_HANDLER = CommandHandler("banned_channels", banned_channels, filters=Filters.group)

dispatcher.add_handler(BAN_CHANNEL_HANDLER)
dispatcher.add_handler(UNBAN_CHANNEL_HANDLER)
dispatcher.add_handler(BANNED_CHANNELS_HANDLER)

PERM_GROUP = 5

dispatcher.add_handler(MessageHandler(Filters.forwarded & Filters.group, kek), PERM_GROUP)
