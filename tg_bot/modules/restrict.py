import tg_bot.modules.sql.notes_sql as sql
from tg_bot.modules.helper_funcs.chat_status import user_admin
from telegram.ext.dispatcher import run_async


@run_async
@user_admin
def restrict_cmd(bot, update, args):
    chat_id = update.effective_chat.id
    if len(args) >= 1:
	restrict_name = args[0]
        if restrict_name  == '/runs' or restrict_name == '/afk':
            sql.restrict_to_db(chat_id, restrict_name)
	    update.effective_message.reply_text("Restricted" + restrict_name)
	else:
            update.effective_message.reply_text("You aren't allowed to disable that!")
            return
    else:
        update.effective_message.reply_text("What should i disable?")
        return

@run_async
@user_admin
def unrestrict(bot, update, args):
    chat_id = update.effective_chat.id
    if len(args) >= 1:
        unrestrict_name = args[0]

        if sql.unrestrict_to_db(chat_id, unrestrict_name):
            update.effective_message.reply_text("Unrestricted the use of" + unrestrict_name)
        else:
            update.effective_message.reply_text("Is it restricted firstly?")



RESTRICT_HANDLER = CommandHandler("restrict", restrict )
UNRESTRICT_HANDLER = CommandHandler("unrestrict", unrestrict)

dispatcher.add_handler(RESTRICT_HANDLER)
dispatcher.add_handler(UNRESTRICT_HANDLER)






