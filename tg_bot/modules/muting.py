import json

import requests
from telegram.ext import CommandHandler
from telegram.ext.dispatcher import run_async
from tg_bot import dispatcher, TOKEN

PWR_TELEGRAM_URL = "https://api.pwrtelegram.xyz/bot"


# TODO make some helper module for these or something idk
def can_delete(bot, update):
    return update.effective_chat.get_member(bot.id).can_delete_messages


def is_user_admin(chat, user_id):
    return chat.get_member(user_id).status == 'administrator'


@run_async
def mute(bot, update):
    chat = update.effective_chat
    message = update.effective_message
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id

        res = bot.restrict_chat_member(chat.id, user_id, can_send_messages=False)
        if res:
            message.reply_text("Muted!")


@run_async
def unmute(bot, update):
    chat = update.effective_chat
    msg = update.effective_message
    words = msg.text.split()
    mentions = [username for username in words if username[0] == '@']
    user = mentions[0]
    res = requests.get(PWR_TELEGRAM_URL + TOKEN + "/getChat", params={'chat_id': user})
    if res.status_code == 200:
        # pprint(json.loads(res.text))
        res = json.loads(res.text).get('result')
        user_id = res.get('id')
        res = bot.restrict_chat_member(chat.id, int(user_id), can_send_messages=True)
        if res:
            msg.reply_text("Unmuted " + user)


MUTE_HANDLER = CommandHandler("mute", mute)
UNMUTE_HANDLER = CommandHandler("unmute", unmute)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
