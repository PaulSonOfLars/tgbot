from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram import ParseMode
from telegram.ext import CommandHandler, run_async, Filters, MessageHandler, CallbackQueryHandler
from telegram.utils.helpers import escape_markdown, mention_html

from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, BAN_STICKER
from tg_bot.__main__ import STATS, USER_INFO
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.helper_funcs.filters import CustomFilters
from threading import Timer

def captcha(bot: Bot, update: Update):
    u = bot.get_chat_member(
        chat_id=update.message.chat_id, user_id=update.effective_user.id)
    bot.restrict_chat_member(chat_id=update.message.chat_id, user_id=update.effective_user.id, can_send_messages=False, can_send_media_messages=False,
                             can_send_other_messages=False, can_add_web_page_previews=False, until_date=367)
    km = [[telegram.InlineKeyboardButton(
        "I'm not a bot", callback_data=u.user.id)]]

    msg = update.message.reply_text("<b>If you are not a bot, press the button below</b>",
                                    reply_markup=telegram.InlineKeyboardMarkup(km), parse_mode=telegram.ParseMode.HTML)

    def check():
        try:
            msg.delete()
            bot.kick_chat_member(chat_id=update.message.chat_id, user_id=update.effective_user.id,
                                 until_date=367)
            bot.unban_chat_member(chat_id=update.message.chat_id,
                                  user_id=update.effective_user.id)
        except Exception:
            pass

    Timer(10.0, check).start()


def pressed(bot, update):
    q = update.callback_query
    if int(q.data) == int(q.from_user.id):
        bot.delete_message(chat_id=q.message.chat_id,
                           message_id=q.message.message_id)
        bot.restrict_chat_member(chat_id=q.message.chat_id, user_id=q.from_user.id, can_send_messages=True, can_send_media_messages=True,
                                 can_send_other_messages=True, can_add_web_page_previews=True)

__mod_name__ = "Captcha"

CAPTCHA_HANDLER = MessageHandler(
        Filters.status_update.new_chat_members, captcha)
dispatcher.add_handler(CAPTCHA_HANDLER)
dispatcher.add_handler(
        CallbackQueryHandler(pressed))