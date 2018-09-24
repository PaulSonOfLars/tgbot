import pyowm
from pyowm import timeutils, exceptions
from telegram import Message, Chat, Update, Bot
from telegram.ext import run_async

from tg_bot import dispatcher, updater, API_WEATHER
from tg_bot.modules.disable import DisableAbleCommandHandler

@run_async
def weather(bot, update, args):
    if len(args) == 0:
        update.effective_message.reply_text("Write a location to check the weather.")
        return

    location = " ".join(args)
    if location.lower() == bot.first_name.lower():
        update.effective_message.reply_text("I will keep an eye on both happy and sad times!")
        bot.send_sticker(update.effective_chat.id, BAN_STICKER)
        return

    try:
        owm = pyowm.OWM(API_WEATHER)
        observation = owm.weather_at_place(location)
        getloc = observation.get_location()
        thelocation = getloc.get_name()
        if thelocation == None:
            thelocation = "Unknown"
        theweather = observation.get_weather()
        temperature = theweather.get_temperature(unit='celsius').get('temp')
        if temperature == None:
            temperature = "Unknown"

        update.message.reply_text("Today in {} is being {}, around {}°C.\n".format(thelocation,
                status, temperature))

    except pyowm.exceptions.not_found_error.NotFoundError:
        update.effective_message.reply_text("Sorry, location not found.")


__help__ = """
 - /weather <city>: get weather info in a particular place
"""

__mod_name__ = "Weather"

WEATHER_HANDLER = DisableAbleCommandHandler("weather", weather, pass_args=True)

dispatcher.add_handler(WEATHER_HANDLER)
