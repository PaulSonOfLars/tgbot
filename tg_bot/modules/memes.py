import random
from telegram import Message, Update, Bot, User
from telegram import MessageEntity
from telegram.ext import Filters, MessageHandler, run_async

from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler


# D A N K module by @deletescape - based on https://github.com/wrxck/mattata/blob/master/plugins/copypasta.mattata

@run_async
def copypasta(bot: Bot, update: Update):
    message = update.effective_message
    emojis = ["😂", "😂", "👌", "✌", "💞", "👍", "👌", "💯", "🎶", "👀", "😂", "👓", "👏", "👐", "🍕", "💥", "🍴", "💦", "💦", "🍑", "🍆", "😩", "😏", "👉👌", "👀", "👅", "😩", "🚰"]
    reply_text = random.choice(emojis)
    b_char = random.choice(message.reply_to_message.text).lower() # choose a random character in the message to be substituted with 🅱️
    for c in message.reply_to_message.text:
        if c == " ":
            reply_text += random.choice(emojis)
        elif c in emojis:
            reply_text += c
            reply_text += random.choice(emojis)
        elif c.lower() == b_char:
            reply_text += "🅱️"
        else:
            if bool(random.getrandbits(1)):
                reply_text += c.upper()
            else:
                reply_text += c.lower()
    reply_text += random.choice(emojis)
    message.reply_to_message.reply_text(reply_text)

# D A N K module by @deletescape

@run_async
def bmoji(bot: Bot, update: Update):
    message = update.effective_message
    b_char = random.choice(message.reply_to_message.text).lower() # choose a random character in the message to be substituted with 🅱️
    reply_text = message.reply_to_message.text.replace(b_char, "🅱️").replace(b_char.upper(), "🅱️")
    message.reply_to_message.reply_text(reply_text)

@run_async
def clapmoji(bot: Bot, update: Update):
    message = update.effective_message
    reply_text = "👏 "
    for i in message.reply_to_message.text:
        if i == " ":
            reply_text += " 👏 "
        else:
            reply_text += i
    reply_text += " 👏"
    message.reply_to_message.reply_text(reply_text)

__help__ = "many memz"  # no help string

__mod_name__ = "Memes"

COPYPASTA_HANDLER = DisableAbleCommandHandler("copypasta", copypasta)
COPYPASTA_ALIAS_HANDLER = DisableAbleCommandHandler("😂", copypasta)
CLAPMOJI_HANDLER = DisableAbleCommandHandler("clapmoji", clapmoji)
CLAPMOJI_ALIAS_HANDLER = DisableAbleCommandHandler("👏", clapmoji)
BMOJI_HANDLER = DisableAbleCommandHandler("🅱️", bmoji)
BMOJI_ALIAS_HANDLER = DisableAbleCommandHandler("️🅱", bmoji)

dispatcher.add_handler(COPYPASTA_HANDLER)
dispatcher.add_handler(COPYPASTA_ALIAS_HANDLER)
dispatcher.add_handler(CLAPMOJI_HANDLER)
dispatcher.add_handler(CLAPMOJI_ALIAS_HANDLER)
dispatcher.add_handler(BMOJI_HANDLER)
dispatcher.add_handler(BMOJI_ALIAS_HANDLER)
