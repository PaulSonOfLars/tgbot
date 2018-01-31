from telegram import TelegramError
from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async

import tg_bot.modules.sql.locks_sql as sql
from tg_bot import dispatcher, SUDO_USERS
from tg_bot.modules.helper_funcs.chat_status import can_delete, is_user_admin, user_not_admin, user_admin, \
    bot_can_delete
from tg_bot.modules.helper_funcs.cust_filters import CustomFilters
from tg_bot.modules.sql import users_sql

LOCK_TYPES = ['sticker', 'audio', 'voice', 'document', 'video', 'contact', 'photo', 'gif']

RESTRICTION_TYPES = ['messages', 'media', 'other', 'previews', 'all']

REST_GROUP = 1


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
def locktypes(bot, update):
    update.effective_message.reply_text("\n - ".join(["Locks: "] + LOCK_TYPES + RESTRICTION_TYPES))


@user_admin
@bot_can_delete
def lock(bot, update, args):
    chat = update.effective_chat
    message = update.effective_message
    if can_delete(chat, bot.id):
        if len(args) >= 1:
            if args[0] in LOCK_TYPES:
                sql.update_lock(chat.id, args[0], locked=True)
                message.reply_text("Locked {} messages for all non-admins!".format(args[0]))

            elif args[0] in RESTRICTION_TYPES:
                sql.update_restriction(chat.id, args[0], locked=True)
                members = users_sql.get_chat_members(chat.id)
                if args[0] == "messages":
                    restr_members(bot, chat.id, members)

                elif args[0] == "media":
                    restr_members(bot, chat.id, members, messages=True)

                elif args[0] == "other":
                    restr_members(bot, chat.id, members, messages=True, media=True)

                elif args[0] == "previews":
                    restr_members(bot, chat.id, members, messages=True, media=True, other=True)

                elif args[0] == "all":
                    restr_members(bot, chat.id, members)

                message.reply_text("Locked {} for all non-admins!".format(args[0]))

            else:
                message.reply_text("What are you trying to lock...? Try /locktypes for the list of lockables")

    else:
        message.reply_text("I'm not an administrator, or haven't got delete rights.")


@run_async
@user_admin
def unlock(bot, update, args):
    chat = update.effective_chat
    message = update.effective_message
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
def del_sticker(bot, update):
    chat = update.effective_chat
    if sql.is_locked(chat.id, "sticker") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
@user_not_admin
def del_audio(bot, update):
    chat = update.effective_chat
    if sql.is_locked(chat.id, "audio") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
@user_not_admin
def del_voice(bot, update):
    chat = update.effective_chat
    if sql.is_locked(chat.id, "voice") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
@user_not_admin
def del_document(bot, update):
    chat = update.effective_chat
    if sql.is_locked(chat.id, "document") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
@user_not_admin
def del_video(bot, update):
    chat = update.effective_chat
    if sql.is_locked(chat.id, "video") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
@user_not_admin
def del_contact(bot, update):
    chat = update.effective_chat
    if sql.is_locked(chat.id, "contact") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
@user_not_admin
def del_photo(bot, update):
    chat = update.effective_chat
    if sql.is_locked(chat.id, "photo") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
@user_not_admin
def del_gif(bot, update):
    chat = update.effective_chat
    if sql.is_locked(chat.id, "gif") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
@user_not_admin
def rest_msg(bot, update):
    msg = update.effective_message
    chat = update.effective_chat
    if sql.is_restr_locked(chat.id, "messages") \
            and can_delete(chat, bot.id) \
            and not is_user_admin(chat, msg.from_user.id):
        msg.delete()
        bot.restrict_chat_member(chat.id, msg.from_user.id,
                                 can_send_messages=False)


@run_async
@user_not_admin
def rest_media(bot, update):
    msg = update.effective_message
    chat = update.effective_chat
    if sql.is_restr_locked(chat.id, "media") \
            and can_delete(chat, bot.id) \
            and not is_user_admin(chat, msg.from_user.id):
        msg.delete()
        bot.restrict_chat_member(chat.id, msg.from_user.id,
                                 can_send_messages=True,
                                 can_send_media_messages=False)


@run_async
@user_not_admin
def rest_other(bot, update):
    msg = update.effective_message
    chat = update.effective_chat
    if sql.is_restr_locked(chat.id, "other") \
            and can_delete(chat, bot.id) \
            and not is_user_admin(chat, msg.from_user.id):
        msg.delete()
        bot.restrict_chat_member(chat.id, msg.from_user.id,
                                 can_send_messages=True,
                                 can_send_media_messages=True,
                                 can_send_other_messages=False)


@run_async
@user_not_admin
def rest_previews(bot, update):
    msg = update.effective_message
    chat = update.effective_chat
    if sql.is_restr_locked(chat.id, "previews") \
            and can_delete(chat, bot.id) \
            and not is_user_admin(chat, msg.from_user.id):
        msg.delete()
        bot.restrict_chat_member(chat.id, msg.from_user.id,
                                 can_send_messages=True,
                                 can_send_media_messages=True,
                                 can_send_other_messages=True,
                                 can_add_web_page_previews=False)


@run_async
@user_admin
def list_locks(bot, update):
    chat = update.effective_chat

    locks = sql.get_locks(chat.id)
    restr = sql.get_restr(chat.id)
    if not (locks or restr):
        res = "There are no current locks in this chat."
    else:
        res = "This is the state of the current chat:\n"
        if locks:
            res += "\n - sticker = {}" \
                   "\n - audio = {}" \
                   "\n - voice = {}" \
                   "\n - document = {}" \
                   "\n - video = {}" \
                   "\n - contact = {}" \
                   "\n - photo = {}" \
                   "\n - gif = {}".format(locks.sticker, locks.audio, locks.voice, locks.document,
                                          locks.video, locks.contact, locks.photo, locks.gif)
        if restr:
            res += "\n - messages = {}" \
                   "\n - media = {}" \
                   "\n - other = {}" \
                   "\n - previews = {}" \
                   "\n - all = {}".format(restr.messages, restr.media, restr.other, restr.preview,
                                          all([restr.messages, restr.media, restr.other, restr.preview]))

    update.effective_message.reply_text(res)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = """
 - /locktypes: a list of possible locktypes
 - /lock <type>: lock items of a certain type (not available in private)
 - /unlock <type>: unlock items of a certain type (not available in private)
 - /locks: the current list of locks in this chat.
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

dispatcher.add_handler(LOCK_HANDLER)
dispatcher.add_handler(UNLOCK_HANDLER)
dispatcher.add_handler(LOCKTYPES_HANDLER)
dispatcher.add_handler(LOCKED_HANDLER)

dispatcher.add_handler(REST_MSG_HANDLER, REST_GROUP)
dispatcher.add_handler(REST_MEDIA_HANDLER, REST_GROUP)
dispatcher.add_handler(REST_OTHERS_HANDLER, REST_GROUP)
# dispatcher.add_handler(REST_PREVIEWS_HANDLER, REST_GROUP) # NOTE: disable, checking for URL's will trigger all urls,

dispatcher.add_handler(GIF_HANDLER)
dispatcher.add_handler(STICKER_HANDLER)
dispatcher.add_handler(AUDIO_HANDLER)
dispatcher.add_handler(VOICE_HANDLER)
dispatcher.add_handler(DOCUMENT_HANDLER)
dispatcher.add_handler(VIDEO_HANDLER)
dispatcher.add_handler(CONTACT_HANDLER)
dispatcher.add_handler(PHOTO_HANDLER)
