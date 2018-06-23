import pyowm
from pyowm import timeutils, exceptions

from typing import Optional, List
from tg_bot import dispatcher, updater, API_WEATHER
from tg_bot.modules.disable import DisableAbleCommandHandler

from telegram import Message, Chat, Update, Bot
from telegram.ext import run_async

@run_async
def cuaca(bot: Bot, update: Update, args: List[str]):
    location = " ".join(args)
    if location.lower() == bot.first_name.lower():
        update.effective_message.reply_text("I will keep an eye on both happy and sad times!")
        bot.send_sticker(update.effective_chat.id, BAN_STICKER)
        return

    try:
        bot.sendChatAction(update.effective_chat.id, "typing") # Bot typing before send message
        owm = pyowm.OWM(API_WEATHER, language='en')
        observation = owm.weather_at_place(location)
        cuacanya = observation.get_weather()
        obs = owm.weather_at_place(location)
        lokasi = obs.get_location()
        lokasinya = lokasi.get_name()
        # statusnya = cuacanya._detailed_status
        temperatur = cuacanya.get_temperature(unit='celsius')['temp']
        fc = owm.three_hours_forecast(location)

        # Simbol cuaca
        statusnya = ""
        cuacaskrg = cuacanya.get_weather_code()
        if cuacaskrg < 232: # Hujan badai
            statusnya += "⛈️ "
        elif cuacaskrg < 321: # Gerimis
            statusnya += "🌧️ "
        elif cuacaskrg < 504: # Hujan terang
            statusnya += "🌦️ "
        elif cuacaskrg < 531: # Hujan berawan
            statusnya += "⛈️ "
        elif cuacaskrg < 622: # Bersalju
            statusnya += "🌨️ "
        elif cuacaskrg < 781: # Atmosfer
            statusnya += "🌪️ "
        elif cuacaskrg < 800: # Cerah
            statusnya += "🌤️ "
        elif cuacaskrg < 801: # Sedikit berawan
             statusnya += "⛅️ "
        elif cuacaskrg < 804: # Berawan
             statusnya += "☁️ "
        statusnya += cuacanya._detailed_status
                    

        update.message.reply_text("Today in {} is being {}, around {}°C.\n".format(lokasinya,
                statusnya, temperatur))

    except pyowm.exceptions.not_found_error.NotFoundError:
        update.effective_message.reply_text("Sorry, location not found.")
    except pyowm.exceptions.api_call_error.APICallError:
        update.effective_message.reply_text("Write a location to check the weather.")
    else:
        return


__help__ = """
 - /weather <city>: get weather info in a particular place
"""

__mod_name__ = "Weather"

CUACA_HANDLER = DisableAbleCommandHandler("weather", cuaca, pass_args=True)

dispatcher.add_handler(CUACA_HANDLER)