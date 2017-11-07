import json
import random
from datetime import datetime

import requests
from telegram import ParseMode
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher, OWNER_ID

RUN_STRINGS = (
    "Where do you think you're going?",
    "Huh? what? did he get away?",
    "ZZzzZZzz... Huh? what? oh, just him again, nevermind.",
    "Get back here!",
    "Not so fast...",
    "Look out for the wall!",
    "Don't leave me alone with them!!",
    "You run, you die.",
    "Run fatboy, run!",
    "Jokes on you, I'm everywhere",
    "You're gonna regret that...",
    "You could also try /kickme, I hear that's fun.",
    "Go bother someone else, no-one here cares.",
    "I hear @MSFJarvis wants to hear more about you.",
    "Please, remind me how much I care?",
    "I'd run faster if I were you.",
    "That's definitely the droid we're looking for.",
    "May the odds be ever in your favour.",
    "Famous last words.",
    "And he disappeared forever, never to be seen again.",
    "\"Oh, look at me! I'm so cool, I can run from a bot!\" - this guy",
    "Yeah yeah, just tap /kickme already.",
    "Here, take this ring and head to Mordor while you're at it.",
    "Legend has it, he's still running...",
    "Unlike Harry Potter, your parents can't protect you from me.",
    "Fear leads to anger. Anger leads to hate. Hate leads to suffering. If you keep running in fear, you might "
    "be the next Vader.",
    "Multiple calculations later, I have decided my interest in your shenanigans is exactly 0."
)

SLAP_TEMPLATES = (
    "{user1} {hits} {user2} with a {item}.",
    "{user1} {hits} {user2} around a bit with a {item}.",
    "{user1} {throws} a {item} at {user2}.",
    "{user1} grabs a {item} and {throws} it at {user2}'s face.",
    "{user1} launches a {item} in {user2}'s general direction.",
    "{user1} sits on {user2}'s face while slamming a {item} into their crotch.",
    "{user1} starts slapping {user2} silly with a {item}.",
    "{user1} pins {user2} down and repeatedly {hits} them with a {item}.",
    "{user1} grabs up a {item} and {hits} {user2} with it.",
    "{user1} ties {user2} to a chair and {throws} a {item} at them.",
)

ITEMS = (
    "cast iron skillet",
    "large trout",
    "baseball bat",
    "cricket bat",
    "wooden cane",
    "nail",
    "printer",
    "shovel",
    "CRT monitor",
    "physics textbook",
    "toaster",
    "portrait of Richard Stallman",
    "television",
    "five ton truck",
    "roll of duct tape",
    "book",
    "laptop",
    "old television",
    "sack of rocks",
    "rainbow trout",
    "rubber chicken",
    "spiked bat",
    "fire extinguisher",
    "heavy rock",
    "chunk of dirt"
)

THROW = (
    "throws",
    "flings",
    "chucks")

HIT = (
    "hits",
    "whacks",
    "slaps",
    "smacks"
)

GMAPS_LOC = "https://maps.googleapis.com/maps/api/geocode/json"
GMAPS_TIME = "https://maps.googleapis.com/maps/api/timezone/json"


@run_async
def runs(bot, update):
    update.effective_message.reply_text(random.choice(RUN_STRINGS))


def slap(bot, update):
    msg = update.effective_message

    if msg.from_user.username:
        curr_user = "@" + escape_markdown(msg.from_user.username)
    else:
        curr_user = "[{}](tg://user?id={})".format(msg.from_user.first_name, msg.from_user.id)

    if msg.reply_to_message:
        user1 = curr_user
        if msg.reply_to_message.from_user.username:
            user2 = "@" + escape_markdown(msg.reply_to_message.from_user.username)
        else:
            user2 = "[{}](tg://user?id={})".format(msg.reply_to_message.from_user.first_name,
                                                   msg.from_user.id)

    else:
        user1 = "[{}](tg://user?id={})".format(bot.first_name, bot.id)
        user2 = curr_user

    temp = random.choice(SLAP_TEMPLATES)
    item = random.choice(ITEMS)
    hit = random.choice(HIT)
    throw = random.choice(THROW)

    repl = temp.format(user1=user1, user2=user2, item=item, hits=hit, throws=throw)

    msg.reply_text(repl, parse_mode=ParseMode.MARKDOWN)


@run_async
def get_bot_ip(bot, update):
    """ Sends the bot's IP address, so as to be able to ssh in if necessary.
        OWNER ONLY.
    """
    res = requests.get("http://ipinfo.io/ip")
    update.message.reply_text(res.text)


@run_async
def get_id(bot, update):
    if update.effective_message.reply_to_message:
        user = update.effective_message.reply_to_message.from_user
        update.effective_message.reply_text(user.username + "'s id is " + str(user.id))
    else:
        chat = update.effective_chat
        update.effective_message.reply_text("This group's id is " + str(chat.id))


@run_async
def get_time(bot, update, args):
    location = " ".join(args)
    if location.lower() == bot.first_name.lower():
        update.effective_message.reply_text("Its always banhammer time for me!")
        bot.send_sticker(update.effective_chat.id, 'CAADAgADOwADPPEcAXkko5EB3YGYAg')
        return

    res = requests.get(GMAPS_LOC, params=dict(address=location))

    if res.status_code == 200:
        loc = json.loads(res.text)
        if loc.get('status') == 'OK':
            lat = loc['results'][0]['geometry']['location']['lat']
            long = loc['results'][0]['geometry']['location']['lng']

            country = None
            city = None

            address_parts = loc['results'][0]['address_components']
            for part in address_parts:
                if 'country' in part['types']:
                    country = part.get('long_name')
                if 'administrative_area_level_1' in part['types'] and not city:
                    city = part.get('long_name')
                if 'locality' in part['types']:
                    city = part.get('long_name')

            if city and country:
                location = "{}, {}".format(city, country)
            elif country:
                location = country

            timenow = int(datetime.utcnow().strftime("%s"))
            res = requests.get(GMAPS_TIME, params=dict(location="{},{}".format(lat, long), timestamp=timenow))
            if res.status_code == 200:
                offset = json.loads(res.text)['dstOffset']
                timestamp = json.loads(res.text)['rawOffset']
                time_there = datetime.fromtimestamp(timenow + timestamp + offset).strftime("%H:%M:%S on %A %d %B")
                update.message.reply_text("It's {} in {}".format(time_there, location))


# /ip is for private use, and /runs is better left undocumented...
__help__ = """
 - /id: get the current group id. If used by replying to a message, gets that user's id.
 - /runs: reply a random string from an array of replies.
 - /slap: slap a user, or get slapped if not a reply
 - /time <place>: gives the local time at the given place
"""

# TODO: /stats
id_handler = CommandHandler("id", get_id)
ip_handler = CommandHandler("ip", get_bot_ip, filters=Filters.chat(OWNER_ID))

time_handler = CommandHandler("time", get_time, pass_args=True)

runs_handler = CommandHandler("runs", runs)
slap_handler = CommandHandler("slap", slap)

dispatcher.add_handler(id_handler)
dispatcher.add_handler(time_handler)
dispatcher.add_handler(runs_handler)
dispatcher.add_handler(slap_handler)
dispatcher.add_handler(ip_handler)
