import pyowm
from pyowm import timeutils, exceptions

from typing import Optional, List
from tg_bot import dispatcher, updater, API_WEATHER
from tg_bot.modules.disable import DisableAbleCommandHandler

from telegram import Message, Chat, Update, Bot
from telegram.ext import run_async

@run_async
def weather(bot: Bot, update: Update, args: List[str]):
    if len(args) >= 1:
        location = " ".join(args)
        if location.lower() == bot.first_name.lower():
            update.effective_message.reply_text("I will keep an eye on both happy and sad times!")
            bot.send_sticker(update.effective_chat.id, BAN_STICKER)
            return

        try:
            owm = pyowm.OWM(API_WEATHER, language='en')
            observation = owm.weather_at_place(location)
            theweather = observation.get_weather()
            getloc = observation.get_location()
            thelocation = getloc.get_name()
            temperature = theweather.get_temperature(unit='celsius')['temp']
            fc = owm.three_hours_forecast(location)

            # Weather symbols
            status = ""
            cuacaskrg = theweather.get_weather_code()
            if cuacaskrg < 232: # Rain storm
                status += "⛈️ "
            elif cuacaskrg < 321: # Drizzle
                status += "🌧️ "
            elif cuacaskrg < 504: # Light rain
                status += "🌦️ "
            elif cuacaskrg < 531: # Cloudy rain
                status += "⛈️ "
            elif cuacaskrg < 622: # Snow
                status += "🌨️ "
            elif cuacaskrg < 781: # Atmosphere
                status += "🌪️ "
            elif cuacaskrg < 800: # Bright
                status += "🌤️ "
            elif cuacaskrg < 801: # A little cloudy
                 status += "⛅️ "
            elif cuacaskrg < 804: # Cloudy
                 status += "☁️ "
            status += theweather._detailed_status
                        

            update.message.reply_text("Today in {} is being {}, around {}°C.\n".format(thelocation,
                    status, temperature))

        except pyowm.exceptions.not_found_error.NotFoundError:
            update.effective_message.reply_text("Sorry, location not found.")
    else:
        update.effective_message.reply_text("Write a location to check the weather.")


__help__ = """
 - /weather <city>: get weather info in a particular place
"""

__mod_name__ = "Weather"

CUACA_HANDLER = DisableAbleCommandHandler("weather", weather, pass_args=True)

dispatcher.add_handler(CUACA_HANDLER)