
from telegram import Message, Update, Bot, User
from telegram.ext import Filters, MessageHandler, run_async

from requests import get

from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot import dispatcher

base_url = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
api_key = 'trnsl.1.1.20180603T023816Z.763b39e3388b46d6.aa9abf45baceb438c96bb1593ce58199cc66c4f1'

@run_async
def translate(bot: Bot, update: Update):
  message = update.effective_message
  text = message.reply_to_message.text
  translation = get(f'{base_url}?key={api_key}&text={text}&lang=en').json()
  
  reply_text = f"Language: {translation['lang']}\nText: {translation['text'][0]}"
  
  message.reply_to_message.reply_text(reply_text)

translate_handler = DisableAbleCommandHandler("tl", translate)

dispatcher.add_handler(translate_handler)
