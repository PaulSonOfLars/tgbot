from telegram import Message, Chat, Update, Bot, User, ParseMode
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
import requests, datetime, json, urllib
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot import dispatcher

@run_async
def devices(bot: Bot, update: Update):
	send = "Devices to be built today are:\n"
	dow = int(datetime.datetime.today().weekday() + 1)
	devices = json.loads(urllib.request.urlopen("https://raw.githubusercontent.com/FireHound/jenkins/o8.1/build-targets.json").read().decode())
	for device in devices:
		if int(device.get("dow")) == dow:
			send = send + "*" + str(device.get("device"))+ "*" + "\n"

	update.effective_message.reply_text(send, parse_mode=ParseMode.MARKDOWN)



devices_handle = DisableAbleCommandHandler("devices", devices)

dispatcher.add_handler(devices_handle)
