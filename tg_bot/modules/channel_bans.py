from typing import Optional, List

from telegram import Chat, Update, Bot
from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async

from tg_bot import dispatcher, SUDO_USERS
from tg_bot.modules.helper_funcs.chat_status import user_not_admin, user_admin, bot_can_delete
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import channel_bans_sql as sql


@user_admin
@bot_can_delete
@loggable
def ban_channel(bot: Bot, update: Update, args: List[str]):
    channel_name = args[0]
    chat_id = update.effective_chat.id
    sql.add_channel_bans(chat_id, channel_name)
    update.effective_message.reply_text("Channel " + channel_name + "was added to ban list")


@run_async
@user_admin
@loggable
def unban_channel(bot: Bot, update: Update, args: List[str]):
    channel_name = args[0]
    chat_id = update.effective_chat.id
    sql.delete_channel_ban(chat_id, channel_name)
    update.effective_message.reply_text("Channel " + channel_name + "was removed from ban list")


@run_async
@user_admin
def banned_channels(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    res = sql.get_channel_bans(chat.id)
    if res is not None:
        res = list(map(lambda x: x.channel_to_ban, res))
        update.effective_message.reply_text("Channels banned in this channel: " + ','.join(res))
    else:
        update.effective_message.reply_text("There are no channels in ban")


@user_admin
@bot_can_delete
@loggable
def global_ban_channel(bot: Bot, update: Update, args: List[str]):
    if int(update.effective_user.id) in SUDO_USERS:
        update.effective_message.reply_text("You are not a sudo user")
    channel_name = args[0]
    sql.add_channel_global_bans(channel_name)
    update.effective_message.reply_text("Channel " + channel_name + "was added to global ban list")


@run_async
@user_admin
@loggable
def global_unban_channel(bot: Bot, update: Update, args: List[str]):
    if int(update.effective_user.id) in SUDO_USERS:
        update.effective_message.reply_text(
            "You are not a sudo user")
    channel_name = args[0]
    sql.delete_channel_global_ban(channel_name)
    update.effective_message.reply_text("Channel " + channel_name + "was removed from global ban list")


@run_async
@user_admin
def global_banned_channels(bot: Bot, update: Update):
    if int(update.effective_user.id) in SUDO_USERS:
        update.effective_message.reply_text(
            "You are not a sudo user")
    res = sql.get_channel_global_bans()
    if res is not None:
        res = list(map(lambda x: x.channel_to_ban, res))
        update.effective_message.reply_text("Channels banned globally: " + ','.join(res))
    else:
        update.effective_message.reply_text("There are no channels in ban")


@run_async
def remove_banned_forwardings(bot: Bot, update: Update):
    if update.effective_message.forward_from_chat is not None:
        forwarder_from_channel_name = update.effective_message.forward_from_chat.username
        is_exists = sql.is_channel_ban_exists(update.effective_chat.id, forwarder_from_channel_name)
        if is_exists:
            update.effective_message.reply_text("Channel " + forwarder_from_channel_name + " banned in this channel")
            update.effective_message.delete()
        is_exists_in_global = sql.is_global_channel_ban_exists(forwarder_from_channel_name)
        if is_exists_in_global:
            update.effective_message.reply_text("Channel " + forwarder_from_channel_name + " banned in global ban list")
            update.effective_message.delete()


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = """

*Admin only:*
 - /banchannel channelname: add channel to list of banned channels in this group
 - /unbanchannel channelname: remove channel from list of banned channels in this group
 - /bannedchannels : show list of all banned channels
 - /globalbanchannel channelname: add channel to global list of banned channels
 - /globalunbanchannel channelname: remove channel from global list of banned channels
 - /globalbannedchannels : show list of all global banned channels
"""

__mod_name__ = "Channel Bans"

BAN_CHANNEL_HANDLER = CommandHandler("banchannel", ban_channel, pass_args=True, filters=Filters.group)
UNBAN_CHANNEL_HANDLER = CommandHandler("unbanchannel", unban_channel, pass_args=True, filters=Filters.group)
BANNED_CHANNELS_HANDLER = CommandHandler("bannedchannels", banned_channels, filters=Filters.group)
GLOBAL_BAN_CHANNEL_HANDLER = CommandHandler("globalbanchannel", ban_channel, pass_args=True, filters=Filters.group)
GLOBAL_UNBAN_CHANNEL_HANDLER = CommandHandler("globalunbanchannel", unban_channel, pass_args=True,
                                              filters=Filters.group)
GLOBAL_BANNED_CHANNELS_HANDLER = CommandHandler("globalbannedchannels", banned_channels, filters=Filters.group)

dispatcher.add_handler(BAN_CHANNEL_HANDLER)
dispatcher.add_handler(UNBAN_CHANNEL_HANDLER)
dispatcher.add_handler(BANNED_CHANNELS_HANDLER)
dispatcher.add_handler(GLOBAL_BAN_CHANNEL_HANDLER)
dispatcher.add_handler(GLOBAL_UNBAN_CHANNEL_HANDLER)
dispatcher.add_handler(GLOBAL_BANNED_CHANNELS_HANDLER)

PERM_GROUP = 5

dispatcher.add_handler(MessageHandler(Filters.forwarded & Filters.group, remove_banned_forwardings), PERM_GROUP)
