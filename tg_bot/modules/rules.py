from telegram import ParseMode
from telegram.ext import CommandHandler, run_async, Filters

import tg_bot.modules.sql.rules_sql as sql
from tg_bot import dispatcher
from tg_bot.modules.helper_funcs import user_admin, markdown_parser


@run_async
def get_rules(bot, update):
    chat_id = update.effective_chat.id
    rules = sql.get_rules(chat_id)
    if rules:
        update.effective_message.reply_text(rules, parse_mode=ParseMode.MARKDOWN)
    else:
        update.effective_message.reply_text("The group admins haven't set any rules for this chat yet. "
                                            "This probably doesn't  mean it's lawless though...!")


@run_async
@user_admin
def set_rules(bot, update):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    raw_text = msg.text
    args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
    if len(args) == 2:
        txt = args[1]
        offset = len(txt) - len(raw_text)  # set correct offset relative to command
        markdown_rules = markdown_parser(txt, entities=msg.parse_entities(), offset=offset)

        sql.set_rules(chat_id, markdown_rules)
        update.effective_message.reply_text("Successfully set rules for this group.")


@run_async
@user_admin
def clear_rules(bot, update):
    chat_id = update.effective_chat.id
    sql.set_rules(chat_id, "")
    update.effective_message.reply_text("Successfully cleared rules!")


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = """
 - /rules: get the rules for this chat.
 - /setrules <your rules here>: set the rules for this chat.
 - /clearrules: clear the rules for this chat.
"""

__name__ = "Rules"


GET_RULES_HANDLER = CommandHandler("rules", get_rules, filters=Filters.group)
SET_RULES_HANDLER = CommandHandler("setrules", set_rules, filters=Filters.group)
RESET_RULES_HANDLER = CommandHandler("clearrules", clear_rules, filters=Filters.group)

dispatcher.add_handler(GET_RULES_HANDLER)
dispatcher.add_handler(SET_RULES_HANDLER)
dispatcher.add_handler(RESET_RULES_HANDLER)
