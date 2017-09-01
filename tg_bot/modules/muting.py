import json

import requests
from telegram.ext import CommandHandler
from telegram.ext.dispatcher import run_async
from tg_bot import dispatcher, TOKEN
from tg_bot.modules.helper_funcs import bot_admin, user_admin

PWR_TELEGRAM_URL = "https://api.pwrtelegram.xyz/bot"


@bot_admin
@user_admin
@run_async
def mute(bot, update, args):
    chat = update.effective_chat
    message = update.effective_message

    if len(args) >= 1 and args[0][0] == '@':
        user = args[0]
        res = requests.get(PWR_TELEGRAM_URL + TOKEN + "/getChat", params={'chat_id': user})
        if res.status_code == 200:
            # pprint(json.loads(res.text))
            res = json.loads(res.text).get('result')
            user_id = res.get('id')
        else:
            message.reply_text("Uh... an external error occured unmuting."
                               "You'll be able to mute them if you reply to that person's message instead.")
            return

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id

    else:
        message.reply_text("You'll need to either give me a username to mute, or reply to someone to be muted.")
        return

    success = bot.restrict_chat_member(chat.id, user_id, can_send_messages=False)
    if success:
        message.reply_text("Muted!")


@bot_admin
@user_admin
@run_async
def unmute(bot, update, args):
    chat = update.effective_chat
    message = update.effective_message

    if len(args) >= 1 and args[0][0] == '@':
        user = args[0]
        res = requests.get(PWR_TELEGRAM_URL + TOKEN + "/getChat", params={'chat_id': user})
        if res.status_code == 200:
            # pprint(json.loads(res.text))
            res = json.loads(res.text).get('result')
            user_id = res.get('id')
            success = bot.restrict_chat_member(chat.id, int(user_id), can_send_messages=True)
            if success:
                message.reply_text("Unmuted " + user)

        else:
            message.reply_text("Uh... an external error occured unmuting.")

__help__ = """
 - /mute: silences a user
 - /unmute <userhandle>: unmutes a user
"""

MUTE_HANDLER = CommandHandler("mute", mute, pass_args=True)
UNMUTE_HANDLER = CommandHandler("unmute", unmute, pass_args=True)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
