from typing import Optional, List

from telegram import Message, Chat, Update, Bot, ParseMode
from telegram import TelegramError, MessageEntity
from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async

import tg_bot.modules.sql.locks_sql as sql
from tg_bot import dispatcher, SUDO_USERS
from tg_bot.modules.helper_funcs.chat_status import can_delete, is_user_admin, user_not_admin, user_admin, \
    bot_can_delete, is_bot_admin
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.sql import users_sql

LOCK_TYPES = ['sticker', 'audio', 'voice', 'document', 'video', 'contact', 'photo', 'gif', 'url', 'bots']

RESTRICTION_TYPES = ['messages', 'media', 'other', 'previews', 'all']

PERM_GROUP = 1
REST_GROUP = 2


# NOT ASYNC
def restr_members(bot, chat_id, members, messages=False, media=False, other=False, previews=False):
    for mem in members:
        if mem.user in SUDO_USERS:
            pass
        try:
            bot.restrict_chat_member(chat_id, mem.user,
                                     can_send_messages=messages,
                                     can_send_media_messages=media,
                                     can_send_other_messages=other,
                                     can_add_web_page_previews=previews)
        except TelegramError:
            pass


# NOT ASYNC
def unrestr_members(bot, chat_id, members, messages=True, media=True, other=True, previews=True):
    for mem in members:
        try:
            bot.restrict_chat_member(chat_id, mem.user,
                                     can_send_messages=messages,
                                     can_send_media_messages=media,
                                     can_send_other_messages=other,
                                     can_add_web_page_previews=previews)
        except TelegramError:
            pass


@run_async
def locktypes(bot: Bot, update: Update):
    update.effective_message.reply_text("\n - ".join(["Locks: "] + LOCK_TYPES + RESTRICTION_TYPES))


@user_admin
@bot_can_delete
def lock(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    if can_delete(chat, bot.id):
        if len(args) >= 1:
            if args[0] in LOCK_TYPES:
                sql.update_lock(chat.id, args[0], locked=True)
                message.reply_text("Locked {} messages for all non-admins!".format(args[0]))

            elif args[0] in RESTRICTION_TYPES:
                sql.update_restriction(chat.id, args[0], locked=True)
                if args[0] == "previews":
                    members = users_sql.get_chat_members(str(chat.id))
                    restr_members(bot, chat.id, members, messages=True, media=True, other=True)

                message.reply_text("Locked {} for all non-admins!".format(args[0]))

            else:
                message.reply_text("What are you trying to lock...? Try /locktypes for the list of lockables")

    else:
        message.reply_text("I'm not an administrator, or haven't got delete rights.")


@run_async
@user_admin
def unlock(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    if is_user_admin(chat, message.from_user.id):
        if len(args) >= 1:
            if args[0] in LOCK_TYPES:
                sql.update_lock(chat.id, args[0], locked=False)
                message.reply_text("Unlocked {} for everyone!".format(args[0]))

            elif args[0] in RESTRICTION_TYPES:
                sql.update_restriction(chat.id, args[0], locked=False)
                members = users_sql.get_chat_members(chat.id)

                if args[0] == "messages":
                    unrestr_members(bot, chat.id, members, media=False, other=False, previews=False)

                elif args[0] == "media":
                    unrestr_members(bot, chat.id, members, other=False, previews=False)

                elif args[0] == "other":
                    unrestr_members(bot, chat.id, members, previews=False)

                elif args[0] == "previews":
                    unrestr_members(bot, chat.id, members)

                elif args[0] == "all":
                    unrestr_members(bot, chat.id, members, True, True, True, True)

                message.reply_text("Unlocked {} for everyone!".format(args[0]))

            else:
                message.reply_text("What are you trying to unlock...? Try /locktypes for the list of lockables")

        else:
            bot.sendMessage(chat.id, "What are you trying to unlock...?")


@run_async
@user_not_admin
def del_sticker(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    if sql.is_locked(chat.id, "sticker") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
@user_not_admin
def del_audio(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    if sql.is_locked(chat.id, "audio") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
@user_not_admin
def del_voice(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    if sql.is_locked(chat.id, "voice") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
@user_not_admin
def del_document(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    if sql.is_locked(chat.id, "document") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
@user_not_admin
def del_video(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    if sql.is_locked(chat.id, "video") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
@user_not_admin
def del_contact(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    if sql.is_locked(chat.id, "contact") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
@user_not_admin
def del_photo(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    if sql.is_locked(chat.id, "photo") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
@user_not_admin
def del_gif(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    if sql.is_locked(chat.id, "gif") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
@user_not_admin
def del_url(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    if sql.is_locked(chat.id, "url") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
@user_not_admin
def remove_bot(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    if sql.is_locked(chat.id, "bots") and is_bot_admin(chat, bot.id):
        new_members = update.effective_message.new_chat_members
        for new_mem in new_members:
            if new_mem.is_bot:
                chat.kick_member(new_mem.id)
                update.effective_message.reply_text("Only admins are allowed to add bots to this chat! Get outta here.")


@run_async
@user_not_admin
def rest_msg(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    if sql.is_restr_locked(chat.id, "messages") \
            and can_delete(chat, bot.id) \
            and not is_user_admin(chat, msg.from_user.id):
        msg.delete()
        bot.restrict_chat_member(chat.id, msg.from_user.id,
                                 can_send_messages=False,
                                 can_send_media_messages=False,
                                 can_send_other_messages=False,
                                 can_add_web_page_previews=False)


@run_async
@user_not_admin
def rest_media(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    if sql.is_restr_locked(chat.id, "media") \
            and can_delete(chat, bot.id) \
            and not is_user_admin(chat, msg.from_user.id):
        msg.delete()
        bot.restrict_chat_member(chat.id, msg.from_user.id,
                                 can_send_messages=True,
                                 can_send_media_messages=False,
                                 can_send_other_messages=False,
                                 can_add_web_page_previews=False)


@run_async
@user_not_admin
def rest_other(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    if sql.is_restr_locked(chat.id, "other") \
            and can_delete(chat, bot.id) \
            and not is_user_admin(chat, msg.from_user.id):
        msg.delete()
        bot.restrict_chat_member(chat.id, msg.from_user.id,
                                 can_send_messages=True,
                                 can_send_media_messages=True,
                                 can_send_other_messages=False,
                                 can_add_web_page_previews=False)


@run_async
@user_not_admin
def rest_previews(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    if sql.is_restr_locked(chat.id, "previews") \
            and can_delete(chat, bot.id) \
            and not is_user_admin(chat, msg.from_user.id):
        bot.restrict_chat_member(chat.id, msg.from_user.id,
                                 can_send_messages=True,
                                 can_send_media_messages=True,
                                 can_send_other_messages=True,
                                 can_add_web_page_previews=False)


def build_lock_message(chat_id):
    locks = sql.get_locks(chat_id)
    restr = sql.get_restr(chat_id)
    if not (locks or restr):
        res = "There are no current locks in this chat."
    else:
        res = "These are the locks in this chat:"
        if locks:
            res += "\n - sticker = `{}`" \
                   "\n - audio = `{}`" \
                   "\n - voice = `{}`" \
                   "\n - document = `{}`" \
                   "\n - video = `{}`" \
                   "\n - contact = `{}`" \
                   "\n - photo = `{}`" \
                   "\n - gif = `{}`" \
                   "\n - url = `{}`" \
                   "\n - bots = `{}`".format(locks.sticker, locks.audio, locks.voice, locks.document,
                                             locks.video, locks.contact, locks.photo, locks.gif, locks.url, locks.bots)
        if restr:
            res += "\n - messages = `{}`" \
                   "\n - media = `{}`" \
                   "\n - other = `{}`" \
                   "\n - previews = `{}`" \
                   "\n - all = `{}`".format(restr.messages, restr.media, restr.other, restr.preview,
                                            all([restr.messages, restr.media, restr.other, restr.preview]))
    return res


@run_async
@user_admin
def list_locks(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]

    res = build_lock_message(chat.id)

    update.effective_message.reply_text(res, parse_mode=ParseMode.MARKDOWN)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return build_lock_message(chat_id)


__help__ = """
 - /locktypes: a list of possible locktypes

*Admin only:*
 - /lock <type>: lock items of a certain type (not available in private)
 - /unlock <type>: unlock items of a certain type (not available in private)
 - /locks: the current list of locks in this chat.

Locks can be used to restrict a group's users.
eg:
Locking urls will auto-delete all messages with urls which haven't been whitelisted, locking stickers will delete all \
stickers, etc.
Locking bots will stop non-admins from adding bots to the chat.
"""

__name__ = "Locks"

GIF = Filters.document & CustomFilters.mime_type("video/mp4")
OTHER = Filters.game | Filters.sticker | GIF
MEDIA = Filters.audio | Filters.document | Filters.video | Filters.voice | Filters.photo
MESSAGES = Filters.text | Filters.contact | Filters.location | Filters.venue | MEDIA | OTHER
PREVIEWS = Filters.entity("url")

LOCKTYPES_HANDLER = CommandHandler("locktypes", locktypes)
LOCK_HANDLER = CommandHandler("lock", lock, pass_args=True, filters=~Filters.private)
UNLOCK_HANDLER = CommandHandler("unlock", unlock, pass_args=True, filters=~Filters.private)
LOCKED_HANDLER = CommandHandler("locks", list_locks, filters=~Filters.private)

REST_MSG_HANDLER = MessageHandler(MESSAGES, rest_msg)
REST_MEDIA_HANDLER = MessageHandler(MEDIA, rest_media)
REST_OTHERS_HANDLER = MessageHandler(OTHER, rest_other)
REST_PREVIEWS_HANDLER = MessageHandler(PREVIEWS, rest_previews)

STICKER_HANDLER = MessageHandler(Filters.sticker, del_sticker)
AUDIO_HANDLER = MessageHandler(Filters.audio, del_audio)
VOICE_HANDLER = MessageHandler(Filters.voice, del_voice)
DOCUMENT_HANDLER = MessageHandler(Filters.document, del_document)
VIDEO_HANDLER = MessageHandler(Filters.video, del_video)
CONTACT_HANDLER = MessageHandler(Filters.contact, del_contact)
PHOTO_HANDLER = MessageHandler(Filters.photo, del_photo)
GIF_HANDLER = MessageHandler(GIF, del_gif)
URL_HANDLER = MessageHandler(Filters.entity(MessageEntity.URL), del_url)
BOT_HANDLER = MessageHandler(Filters.status_update.new_chat_members, remove_bot)

dispatcher.add_handler(LOCK_HANDLER)
dispatcher.add_handler(UNLOCK_HANDLER)
dispatcher.add_handler(LOCKTYPES_HANDLER)
dispatcher.add_handler(LOCKED_HANDLER)

dispatcher.add_handler(REST_MSG_HANDLER, REST_GROUP)
dispatcher.add_handler(REST_MEDIA_HANDLER, REST_GROUP)
dispatcher.add_handler(REST_OTHERS_HANDLER, REST_GROUP)
dispatcher.add_handler(REST_PREVIEWS_HANDLER, REST_GROUP)

dispatcher.add_handler(GIF_HANDLER, PERM_GROUP)  # be at top, before doc handler
dispatcher.add_handler(STICKER_HANDLER, PERM_GROUP)
dispatcher.add_handler(AUDIO_HANDLER, PERM_GROUP)
dispatcher.add_handler(VOICE_HANDLER, PERM_GROUP)
dispatcher.add_handler(DOCUMENT_HANDLER, PERM_GROUP)
dispatcher.add_handler(VIDEO_HANDLER, PERM_GROUP)
dispatcher.add_handler(CONTACT_HANDLER, PERM_GROUP)
dispatcher.add_handler(PHOTO_HANDLER, PERM_GROUP)
dispatcher.add_handler(URL_HANDLER, PERM_GROUP)
dispatcher.add_handler(BOT_HANDLER, PERM_GROUP)
