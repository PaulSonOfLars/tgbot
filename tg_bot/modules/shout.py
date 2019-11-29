from telegram import Update, Bot
from telegram.ext import run_async

from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot import dispatcher

@run_async
def shout(bot: Bot, update: Update, args):
    msg = "```"
    text = " ".join(args)
    result = []
    result.append(' '.join([s for s in text]))
    for pos, symbol in enumerate(text[1:]):
        result.append(symbol + ' ' + '  ' * pos + symbol)
    result = list("\n".join(result))
    result[0] = text[0]
    result = "".join(result)
    msg = "```\n" + result + "```"
    return update.effective_message.reply_text(msg, parse_mode="MARKDOWN")
    
__help__ = """
 A little piece of fun wording! Give a loud shout out in the chatroom.
 
 i.e /shout HELP, bot replies with huge coded HELP letters within the square. 
 
 - /shout <keyword>: write anything you want to give loud shout.
    ```
    t e s t
    e e
    s   s
    t     t
    ```
"""

__mod_name__ = "Shout"

SHOUT_HANDLER = DisableAbleCommandHandler("shout", shout, pass_args=True)

dispatcher.add_handler(SHOUT_HANDLER)
