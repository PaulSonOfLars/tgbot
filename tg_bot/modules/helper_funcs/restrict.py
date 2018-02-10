from tg_bot.modules.sql.restrict_sql import check_if_restricted
from functools import wraps


def restrict(func):
    @wraps(func)
    def restrict_check(bot, update, *args, **kwargs):
	rstrct = update.effective_message.text.split(None, 2)
	cmd_to_restrict = rstrct[0]
	cchat = update.effective_chat.chat_id
	restriction_check = check_if_restricted(cchat, cmd_to_restrict)
        if restriction_check:
            update.effective_message.reply_text("This command is disabled!")
        else:
            func(bot, update, *args, **kwargs)

    return restrict_check


