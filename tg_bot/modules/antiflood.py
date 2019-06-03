import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, CommandHandler, run_async
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import is_user_admin, user_admin, can_restrict, can_delete
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import antiflood_sql as sql

FLOOD_GROUP = 3


@run_async
@loggable
def check_flood(bot: Bot, update: Update) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]
    limit = sql.get_flood_limit(chat.id)

    if not user:  # ignore channels
        return ""

    # ignore admins
    if is_user_admin(chat, user.id):
        sql.update_flood(chat.id, None)
        return ""

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""
    
    soft_flood = sql.get_flood_strength(chat.id)
    if soft_flood:  # kick
        chat.unban_member(user.id)
        reply = "Wonderful, I don't like your flooding. Get out!" \
                " {} has been kicked!".format(mention_html(user.id, user.first_name))

    else:  # ban
        chat.kick_member(user.id)
        reply = "Frankly, I like to leave the flooding to natural disasters." \
                " {} has been banned!".format(mention_html(user.id, user.first_name))
    try:
        keyboard = []
        msg.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        msg.delete()
        
        log = "<b>{}:</b>" \
              "\n#FLOOD_CONTROL" \
              "\n<b>• User:</b> {}" \
              "\n<b>• ID:</b> <code>{}</code>".format(html.escape(chat.title), mention_html(user.id, user.first_name), user.id)
        
        if soft_flood:
           log +="\n<b>• Action:</b> kicked"
        
        else:
           log +="\n<b>• Action:</b> banned"
        
        log +="\n<b>• Reason:</b> Exceeded flood limit of {} consecutive messages.".format(limit)
                                                                               
        
        return log

    except BadRequest:
        msg.reply_text("I can't kick people here, give me permissions first! Until then, I'll disable anti-flood.")
        sql.set_flood(chat.id, 0)
        return "<b>{}:</b>" \
               "\n#INFO" \
               "\nDon't have kick permissions, so automatically disabled anti-flood.".format(chat.title)


@run_async
@user_admin
@can_restrict
@loggable
def set_flood(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    if len(args) >= 1:
        val = args[0].lower()
        if val == "off" or val == "no" or val == "0":
            sql.set_flood(chat.id, 0)
            message.reply_text("Anti-flood has been disabled.")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat.id, 0)
                message.reply_text("Anti-flood has been disabled.")
                return "<b>{}:</b>" \
                       "\n#SETFLOOD" \
                       "\n<b>• Admin:</b> {}" \
                       "\nDisabled Anti-flood.".format(html.escape(chat.title), mention_html(user.id, user.first_name))

            elif amount < 1:
                message.reply_text("Anti-flood has to be either 0 (disabled) or least 1")
                return ""

            else:
                sql.set_flood(chat.id, amount)
                message.reply_text("Anti-flood has been updated and set to {}".format(amount))
                return "<b>{}:</b>" \
                       "\n#SETFLOOD" \
                       "\n<b>• Admin:</b> {}" \
                       "\nSet anti-flood to <code>{}</code>.".format(html.escape(chat.title),
                                                                    mention_html(user.id, user.first_name), amount)

        else:
            message.reply_text("Unrecognised argument - please use a number, 'off', or 'no'.")
    else:
        message.reply_text("Give me an argument! Set a number to enforce against consecutive spams.\n" \
                           "i.e `/setflood 5`: to control consecutive of messages.", parse_mode=ParseMode.MARKDOWN)
    return ""


@run_async
def flood(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message # type: Optional[Message]
    limit = sql.get_flood_limit(chat.id)
    if limit == 0:
        update.effective_message.reply_text("I'm not currently enforcing flood control!")
    else:
        soft_flood = sql.get_flood_strength(chat.id)
        if soft_flood:
            msg.reply_text("I'm currently kicking users out if they send more than {} " 
                           "consecutive messages. They will able to join again!".format(limit, parse_mode=ParseMode.MARKDOWN))
        else:
            msg.reply_text("I'm currently banning users if they send more than {} " 
                           "consecutive messages.".format(limit, parse_mode=ParseMode.MARKDOWN))

@run_async
@user_admin
@loggable
def set_flood_strength(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    if args:
        if args[0].lower() in ("on", "yes"):
            sql.set_flood_strength(chat.id, False)
            msg.reply_text("Exceeding consecutive flood limit will result in a ban!")
            return "<b>{}:</b>\n" \
                   "<b>• Admin:</b> {}\n" \
                   "Has enabled strong flood and users will be banned.".format(html.escape(chat.title),
                                                                            mention_html(user.id, user.first_name))

        elif args[0].lower() in ("off", "no"):
            sql.set_flood_strength(chat.id, True)
            msg.reply_text("Exceeding consecutive flood limit will result in a kick, Users will able to join back.")
            return "<b>{}:</b>\n" \
                   "<b>• Admin:</b> {}\n" \
                   "Has disabled strong flood and users will only be kicked.".format(html.escape(chat.title),
                                                                                  mention_html(user.id,
                                                                                               user.first_name))

        else:
            msg.reply_text("I only understand on/yes/no/off!")
    else:
        soft_flood = sql.get_flood_strength(chat.id)
        if soft_flood == True:
            msg.reply_text("Flood strength is currently set to *kick* users when they exceed the limits, "
                           "user will be kicked.",
                           parse_mode=ParseMode.MARKDOWN)
                 
        elif soft_flood:
            msg.reply_text("The default configuration for flood control is currently set as a ban.",
                           parse_mode=ParseMode.MARKDOWN)
        
        elif soft_flood == False:
            msg.reply_text("Flood strength is currently set to *ban* users when they exceed the limits, "
                           "user will be banned.",
                           parse_mode=ParseMode.MARKDOWN)
    return ""

def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    soft_flood = sql.get_flood_strength(chat_id)
    if limit == 0:
        return "*Not* currently enforcing flood control."
    else:
        if soft_flood:
            return "Anti-flood is set to `{}` messages and *KICK* if exceeded.".format(limit)
        else:
            return "Anti-flood is set to `{}` messages and *BAN* if exceeded.".format(limit)
__help__ = """
You know how sometimes, people join, send 100 messages, and ruin your chat? With antiflood, that happens no more!

Antiflood allows you to take action on users that send more than x messages in a row. Exceeding the set flood \
will result in banning or kicking the user.

 - /flood: Get the current flood control setting

*Admin only:*
 - /setflood <int/'no'/'off'>: enables or disables flood control
 - /strongflood <on/yes/off/no>: If set to on, exceeding the flood limit will result in a ban. Else, will just kick.
"""

__mod_name__ = "Anti-Flood"

FLOOD_BAN_HANDLER = MessageHandler(Filters.all & ~Filters.status_update & Filters.group, check_flood)
SET_FLOOD_HANDLER = CommandHandler("setflood", set_flood, pass_args=True, filters=Filters.group)
FLOOD_HANDLER = CommandHandler("flood", flood, filters=Filters.group)
FLOOD_STRENGTH_HANDLER = CommandHandler("strongflood", set_flood_strength, pass_args=True, filters=Filters.group)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)
dispatcher.add_handler(FLOOD_STRENGTH_HANDLER)
