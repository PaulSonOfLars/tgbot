from telegram.ext import run_async, Filters
from telegram import Message, Chat, Update, Bot, MessageEntity
from tg_bot import dispatcher
from tg_bot.modules.disable import CommandHandler

normiefont = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
weebyfont = ['卂','乃','匚','刀','乇','下','厶','卄','工','丁','长','乚','从','𠘨','口','尸','㔿','尺','丂','丅','凵','リ','山','乂','丫','乙']

@run_async
def weebify(bot: Bot, update: Update, args):

  string = '  '.join(args).lower()
  for normiecharacter in string:
    if normiecharacter in normiefont:
      weebycharacter = weebyfont[normiefont.index(normiecharacter)]
      string = string.replace(normiecharacter, weebycharacter)

  message = update.effective_message
  if message.reply_to_message:
    message.reply_to_message.reply_text(string)
  else:
    message.reply_text(string)

WEEBIFY_HANDLER = CommandHandler("weebify", weebify, pass_args=True)

dispatcher.add_handler(WEEBIFY_HANDLER)
