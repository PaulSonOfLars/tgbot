from telegram.ext import CommandHandler, run_async

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs import user_admin, bot_admin
from tg_bot.modules.sql import warns_sql as sql
from tg_bot.modules.users import get_user_id


@run_async
@user_admin
@bot_admin
def warn(bot, update):
    message = update.effective_message
    args = message.text.split(None, 2)  # use python's maxsplit to separate Cmd, warn recipient, and warn reason

    if len(args) >= 2 and args[1][0] == '@':
        user = args[1]
        user_id = get_user_id(user)
        if not user_id:
            message.reply_text("I don't have that user in my db. You'll be able to interact with them if "
                               "you reply to that person's message instead.")
            return
    elif message.entities and message.parse_entities('text_mention'):
        entities = message.parse_entities('text_mention')
        for e in entities:
            user_id = e.user.id
            break
        else:
            return
    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id

    else:
        return

    chat = update.effective_chat

    if len(args) >= 3:
        reason = args[2]
    else:
        reason = ""

    user_warned = sql.warn_user(user_id, chat.id, reason)
    if user_warned.num_warns > 3:
        res = chat.kick_member(user_id)
        if res:
            bot.send_sticker(chat.id, 'CAADAgADOwADPPEcAXkko5EB3YGYAg')  # banhammer marie sticker
            message.reply_text("Banned!")
            sql.reset_warns(user_id, chat.id)
        else:
            message.reply_text("An error occured, I couldn't ban this person!")


def mywarns(bot, update):
    warned_user = sql.get_warns(update.effective_user.id, update.effective_chat.id)
    if warned_user.num_warns == 0:
        if warned_user.reasons:
            text = "You have {} warnings, for the following reasons:".format(warned_user.num_warns)
            for reason in warned_user.reasons:
                text += "\n - {}".format(reason)
            # TODO: Check length of text to send.
            update.effective_message.reply_text(text)
        else:
            update.effective_message.reply_text("You have {} warnings.".format(warned_user.num_warns))
    else:
        update.effective_message.reply_text("You haven't got any warnings!")


WARN_HANDLER = CommandHandler("warn", warn)
MYWARNS_HANDLER = CommandHandler("mywarns", mywarns)

dispatcher.add_handler(WARN_HANDLER)
dispatcher.add_handler(MYWARNS_HANDLER)
