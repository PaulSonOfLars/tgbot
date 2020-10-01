from typing import Optional

from telegram import Message, Update, Bot, User
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown

import tg_bot.modules.sql.rules_sql as sql
from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import user_admin
from tg_bot.modules.helper_funcs.string_handling import markdown_parser


@run_async
def get_rules(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    send_rules(update, chat_id)


# Do not async - not from a handler
def send_rules(update, chat_id, from_pm=False):
    bot = dispatcher.bot
    user = update.effective_user  # type: Optional[User]
    try:
        chat = bot.get_chat(chat_id)
    except BadRequest as excp:
        if excp.message == "Chat not found" and from_pm:
            bot.send_message(
                user.id,
                "Lo shortcut delle regole per questa chat non è stato impostato correttamente. Usa @admin "
                "per contattare gli admin.",
            )
            return
        else:
            raise

    rules = sql.get_rules(chat_id)
    text = "Ecco il regolamento di *{}*:\n\n{}".format(
        escape_markdown(chat.title), rules
    )

    if from_pm and rules:
        bot.send_message(
            user.id,
            text,
            parse_mode=ParseMode.MARKDOWN,
            preview=False,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Leggi il CoC",
                            url="https://telegra.ph/CoC-di-PythonItalia-07-09",
                        )
                    ]
                ]
            ),
        )
    elif from_pm:
        bot.send_message(
            user.id,
            "Gli admin non hanno ancora impostato le regole del gruppo. "
            "Per favore attieniti alle regole di rispetto reciproco che vigono in ogni chat online.",
        )
    elif rules:
        update.effective_message.reply_text(
            "Contattami per avere la lista delle regole.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Rules",
                            url="t.me/{}?start={}".format(bot.username, chat_id),
                        )
                    ]
                ]
            ),
        )
    else:
        update.effective_message.reply_text(
            "Il gruppo non ha ancora nessuna regola impostata. "
            "Per favore attieniti alle regole di rispetto reciproco che vigono in ogni chat online."
        )


@run_async
@user_admin
def set_rules(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    raw_text = msg.text
    args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
    if len(args) == 2:
        txt = args[1]
        offset = len(txt) - len(raw_text)  # set correct offset relative to command
        markdown_rules = markdown_parser(
            txt, entities=msg.parse_entities(), offset=offset
        )

        sql.set_rules(chat_id, markdown_rules)
        update.effective_message.reply_text("Regola aggiunta con successo.")


@run_async
@user_admin
def clear_rules(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    sql.set_rules(chat_id, "")
    update.effective_message.reply_text("Regole cancellate con successo!")


def __stats__():
    return "{} ha regole impostate.".format(sql.num_chats())


def __import_data__(chat_id, data):
    # set chat rules
    rules = data.get("info", {}).get("rules", "")
    sql.set_rules(chat_id, rules)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "Questa chat ha le seguenti regole: `{}`".format(
        bool(sql.get_rules(chat_id))
    )


__help__ = """
 - /rules: ottieni le regole per questa chat.

*Admin only:*
 - /setrules <your rules here>: imposta una regola per la chat.
 - /clearrules: cancella le regole della chat.
"""

__mod_name__ = "Rules"

GET_RULES_HANDLER = CommandHandler("rules", get_rules, filters=Filters.group)
SET_RULES_HANDLER = CommandHandler("setrules", set_rules, filters=Filters.group)
RESET_RULES_HANDLER = CommandHandler("clearrules", clear_rules, filters=Filters.group)

dispatcher.add_handler(GET_RULES_HANDLER)
dispatcher.add_handler(SET_RULES_HANDLER)
dispatcher.add_handler(RESET_RULES_HANDLER)
