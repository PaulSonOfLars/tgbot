import html
import json
import random
from datetime import datetime
from typing import Optional, List

import requests
from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram import ParseMode
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown, mention_html

from tg_bot import (
    dispatcher,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    WHITELIST_USERS,
    BAN_STICKER,
)
from tg_bot.__main__ import GDPR
from tg_bot.__main__ import STATS, USER_INFO
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.helper_funcs.filters import CustomFilters

RUN_STRINGS = (
    "Dove pensi di poter andare?",
    "Huh? cosa? Se ne sono andati?",
    "ZZzzZZzz... Huh? Cosa? oh, ancora loro, amen.",
    "Torna qui!",
    "Non così velocemente...",
    "Non lasciarmi da solo con loro!!",
    "Se corri, muori.",
    "Scherzi a parte, io sono ovunque",
    "Ti pentirai di questa cosa...",
    "Devi assolutamente provare il comando /kickme, ho sentito dire che è divertente.",
    "Vai da qualche altra parte.. Qui non interessa a nessuno.",
    "Puoi correre, ma non puoi nasconderti.",
    "Tutto qui?",
    "Sono dietro di te..",
    "Sei in buona compagnia!",
    "Possiamo usare le maniere buone.. o quelle *cattive*.",
    "Non ci arrivi, vero?",
    "Yeah, faresti meglio a correre!",
    "Scusami, mi potresti ricordare quanto me ne importa?",
    "Scapperei più velocemente se fossi in te",
    "Ultime parole famose.",
    "E così sparì, senza farsi più rivedere.",
    "Yeah yeah, meglio se fai /kickme a questo punto.",
    "Diversamente da Harry Potter, i tuoi genitori non possono proteggerti qui.",
    "sii il prossimo Vader.",
    "Dopo migliaia di calcoli, l'uso dei cluster di google e microsoft, ho capito che di questo argomento mi interessa meno di 0 (che è davvero poco)",
    "Hasta la vista, baby.",
    "Non si corre nei corridoi!",
    "Francamente, mio caro, non me ne frega assolutamente niente.",
    "Non puoi CAPIRE la verità!",
    "Hey, guardali! Stanno scappando da un inevitabile banhammer... Carini.",
)

SLAP_TEMPLATES = (
    "{user1} {hits} {user2} con un {item}.",
    "{user1} {hits} {user2} in faccia con un {item}.",
    "{user1} {hits} {user2} un pochino con un {item}.",
    "{user1} {throws} un {item} a {user2}.",
    "{user1} grabs un {item} e {throws} questo in faccia a {user2}.",
    "{user1} ha lanciato un {item} a {user2}.",
    "{user1} ha cominciato a schiaffeggiare {user2} violentemente con un {item}.",
    "{user1} ha preso un {item} e {hits} {user2} con questo.",
    "{user1} ha spintonato in modo gentile {user2} per insegnarli a nuotare nella lava.",
)

ITEMS = (
    "padella di ferro",
    "grossa trota",
    "mazza da baseball",
    "mazza da cricket",
    "canna di legno",
    "chiodo",
    "stampante",
    "pala",
    "CRT monitor",
    "libro di fisica",
    "toaster",
    "album di Richard Stallman",
    "televisione",
    "camion di 5 tons",
    "rotolo di nastro adesivo",
    "libro",
    "laptop",
    "vecchia televisione",
    "sacco di rocce",
    "trota arcobaleno",
    "pipistrello",
    "estintore",
    "pezzo di roccia pesante",
    "pezzo di terra",
    "alveare",
    "pezzo di carne andata a male",
    "birra",
    "carico di mattoni",
)

THROW = ("getta", "scaglia", "lancia", "scaraventa")

HIT = ("colpisce", "bastona", "sciaffeggia", "spacca", "colpisce con violenza")

GMAPS_LOC = "https://maps.googleapis.com/maps/api/geocode/json"
GMAPS_TIME = "https://maps.googleapis.com/maps/api/timezone/json"


@run_async
def runs(bot: Bot, update: Update):
    update.effective_message.reply_text(random.choice(RUN_STRINGS))


@run_async
def slap(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]

    # reply to correct message
    reply_text = (
        msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text
    )

    # get user who sent message
    if msg.from_user.username:
        curr_user = "@" + escape_markdown(msg.from_user.username)
    else:
        curr_user = "[{}](tg://user?id={})".format(
            msg.from_user.first_name, msg.from_user.id
        )

    user_id = extract_user(update.effective_message, args)
    if user_id:
        slapped_user = bot.get_chat(user_id)
        user1 = curr_user
        if slapped_user.username:
            user2 = "@" + escape_markdown(slapped_user.username)
        else:
            user2 = "[{}](tg://user?id={})".format(
                slapped_user.first_name, slapped_user.id
            )

    # if no target found, bot targets the sender
    else:
        user1 = "[{}](tg://user?id={})".format(bot.first_name, bot.id)
        user2 = curr_user

    temp = random.choice(SLAP_TEMPLATES)
    item = random.choice(ITEMS)
    hit = random.choice(HIT)
    throw = random.choice(THROW)

    repl = temp.format(user1=user1, user2=user2, item=item, hits=hit, throws=throw)

    reply_text(repl, parse_mode=ParseMode.MARKDOWN)


@run_async
def get_bot_ip(bot: Bot, update: Update):
    """ Sends the bot's IP address, so as to be able to ssh in if necessary.
        OWNER ONLY.
    """
    res = requests.get("http://ipinfo.io/ip")
    update.message.reply_text(res.text)


@run_async
def get_id(bot: Bot, update: Update, args: List[str]):
    user_id = extract_user(update.effective_message, args)
    if user_id:
        if (
                update.effective_message.reply_to_message
                and update.effective_message.reply_to_message.forward_from
        ):
            user1 = update.effective_message.reply_to_message.from_user
            user2 = update.effective_message.reply_to_message.forward_from
            update.effective_message.reply_text(
                "Il mittente originale, {}, ha un ID di `{}`.\nIl forwarder, {}, ha un ID di `{}`.".format(
                    escape_markdown(user2.first_name),
                    user2.id,
                    escape_markdown(user1.first_name),
                    user1.id,
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            user = bot.get_chat(user_id)
            update.effective_message.reply_text(
                "L'id di {} è `{}`.".format(escape_markdown(user.first_name), user.id),
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        chat = update.effective_chat  # type: Optional[Chat]
        if chat.type == "private":
            update.effective_message.reply_text(
                "Il tuo id è `{}`.".format(chat.id), parse_mode=ParseMode.MARKDOWN
            )

        else:
            update.effective_message.reply_text(
                "L'id di questo gruppo è `{}`.".format(chat.id),
                parse_mode=ParseMode.MARKDOWN,
            )


@run_async
def info(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]
    user_id = extract_user(update.effective_message, args)

    if user_id:
        user = bot.get_chat(user_id)

    elif not msg.reply_to_message and not args:
        user = msg.from_user

    elif not msg.reply_to_message and (
            not args
            or (
                    len(args) >= 1
                    and not args[0].startswith("@")
                    and not args[0].isdigit()
                    and not msg.parse_entities([MessageEntity.TEXT_MENTION])
            )
    ):
        msg.reply_text("Non posso ricavare l'utente in questo modo.")
        return

    else:
        return

    text = (
        "<b>Informazioni utente</b>:"
        "\nID: <code>{}</code>"
        "\nNome: {}".format(user.id, html.escape(user.first_name))
    )

    if user.last_name:
        text += "\nCognome: {}".format(html.escape(user.last_name))

    if user.username:
        text += "\nUsername: @{}".format(html.escape(user.username))

    text += "\nLink utente permanente: {}".format(mention_html(user.id, "link"))

    if user.id == OWNER_ID:
        text += "\n\nQuesta persona è il mio proprietario - Non gli farei mai nulla!"
    else:
        if user.id in SUDO_USERS:
            text += (
                "\nQuesto utente è uno dei miei sudo user! "
                "Forte quasi come il mio proprietario - quindi stai attento."
            )
        else:
            if user.id in SUPPORT_USERS:
                text += (
                    "\nQuesta persona è uno dei miei supporter! "
                    "Non proprio uno sudo user, ma può ancora gbannarti."
                )

            if user.id in WHITELIST_USERS:
                text += (
                    "\nQuesta persona è stata whitelistata! "
                    "Questo significa che non posso bannare/kickkare."
                )

    for mod in USER_INFO:
        mod_info = mod.__user_info__(user.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def get_time(bot: Bot, update: Update, args: List[str]):
    location = " ".join(args)
    if location.lower() == bot.first_name.lower():
        update.effective_message.reply_text("Ohh, è sempre tempo di banhammer per me!")
        bot.send_sticker(update.effective_chat.id, BAN_STICKER)
        return

    res = requests.get(GMAPS_LOC, params=dict(address=location))

    if res.status_code == 200:
        loc = json.loads(res.text)
        if loc.get("status") == "OK":
            lat = loc["results"][0]["geometry"]["location"]["lat"]
            long = loc["results"][0]["geometry"]["location"]["lng"]

            country = None
            city = None

            address_parts = loc["results"][0]["address_components"]
            for part in address_parts:
                if "country" in part["types"]:
                    country = part.get("long_name")
                if "administrative_area_level_1" in part["types"] and not city:
                    city = part.get("long_name")
                if "locality" in part["types"]:
                    city = part.get("long_name")

            if city and country:
                location = "{}, {}".format(city, country)
            elif country:
                location = country

            timenow = int(datetime.utcnow().timestamp())
            res = requests.get(
                GMAPS_TIME,
                params=dict(location="{},{}".format(lat, long), timestamp=timenow),
            )
            if res.status_code == 200:
                offset = json.loads(res.text)["dstOffset"]
                timestamp = json.loads(res.text)["rawOffset"]
                time_there = datetime.fromtimestamp(
                    timenow + timestamp + offset
                ).strftime("%H:%M:%S on %A %d %B")
                update.message.reply_text("It's {} in {}".format(time_there, location))


@run_async
def echo(bot: Bot, update: Update):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    if message.reply_to_message:
        message.reply_to_message.reply_text(args[1])
    else:
        message.reply_text(args[1], quote=False)
    message.delete()


@run_async
def gdpr(bot: Bot, update: Update):
    update.effective_message.reply_text(
        "Elimino informazioni che possono identificarti..."
    )
    for mod in GDPR:
        mod.__gdpr__(update.effective_user.id)

    update.effective_message.reply_text(
        "Le tue informazioni personali sono state eliminate.\n\nNota bene che questo non ti unbannerà "
        "da nessuna chat. "
        "Flooding, warns, e gbans sono anch'essi salvati secondo "
        "[questo](https://ico.org.uk/for-organisations/guide-to-the-general-data-protection-regulation-gdpr/individual-rights/right-to-erasure/), "
        "che afferma chiaramente che il diritto alla cancellazione non si applica "
        "\"per l'esecuzione di un compito svolto nell'interesse pubblico\", come nel "
        "caso per i dati di cui sopra.",
        parse_mode=ParseMode.MARKDOWN,
    )


MARKDOWN_HELP = """
Markdown è uno strumento di formattazione molto potente supportato dal Telegram. {} ha alcuni miglioramenti, per essere sicuro che \
i messaggi salvati vengono analizzati correttamente e per consentire di creare pulsanti.

- <code> _italic _ </ code>: il wrapping del testo con '_' produrrà il testo in corsivo
- <code> * bold * </ code>: il wrapping del testo con '*' produce testo in grassetto
- <code> `code` </ code>: il wrapping del testo con '`' produrrà un testo monospaced, noto anche come 'code'
- <code> [sometext](someURL) </ code>: questo creerà un link - il messaggio mostrerà solo <code> sometext </ code>, \
e toccandolo si aprirà la pagina su <code> someURL </ code>.
EG: <code> [test] (example.com) </ code>

- <code> [buttontext](buttonurl: someURL) </ code>: questo è un miglioramento speciale per consentire agli utenti di avere Telegram \
pulsanti nel loro markdown. <code> buttontext </ code> sarà ciò che viene visualizzato sul pulsante e <code> someurl </ code> \
sarà l'url che verrà aperto.
EG: <code> [Questo è un pulsante](buttonurl: example.com) </ code>

Se vuoi più pulsanti sulla stessa riga, usa :same, in quanto tale:
<Code> [uno] (buttonurl: //example.com)
[Due] (buttonurl: //google.com: idem) </ code>
Questo creerà due pulsanti su una singola riga, invece di un pulsante per riga.

Tieni presente che il tuo messaggio <b> DEVE </ b> contenere del testo diverso da un semplice pulsante!
""".format(
    dispatcher.bot.first_name
)


@run_async
def markdown_help(bot: Bot, update: Update):
    update.effective_message.reply_text(MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        "Try forwarding the following message to me, and you'll see!"
    )
    update.effective_message.reply_text(
        "/save test This is a markdown test. _italics_, *bold*, `code`, "
        "[URL](example.com) [button](buttonurl:github.com) "
        "[button2](buttonurl://google.com:same)"
    )


@run_async
def stats(bot: Bot, update: Update):
    update.effective_message.reply_text(
        "Stats attuali:\n" + "\n".join([mod.__stats__() for mod in STATS])
    )


# /ip is for private use
__help__ = """
 - /id: ottieni l'id del gruppo attuale. Se utilizzato rispondendo a un messaggio, ottieni l'id dell'utente.
 - /runs: rispondi con una stringa casuale da una serie di risposte.
 - /slap: schiaffeggiare un utente, o essere schiaffeggiato se non una risposta.
 - /info: ottenere informazioni su un utente.
 - /gdpr: cancella le tue informazioni dal database del bot. Solo chat private.

 - /markdownhelp: un rapido riepilogo di come funziona il markdown di Telegram - può essere chiamato solo in chat private.
"""

__mod_name__ = "Misc"

ID_HANDLER = DisableAbleCommandHandler("id", get_id, pass_args=True)
IP_HANDLER = CommandHandler("ip", get_bot_ip, filters=Filters.chat(OWNER_ID))

TIME_HANDLER = CommandHandler("time", get_time, pass_args=True)

RUNS_HANDLER = DisableAbleCommandHandler("runs", runs)
SLAP_HANDLER = DisableAbleCommandHandler("slap", slap, pass_args=True)
INFO_HANDLER = DisableAbleCommandHandler("info", info, pass_args=True)

ECHO_HANDLER = CommandHandler("echo", echo, filters=Filters.user(OWNER_ID))
MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help, filters=Filters.private)

STATS_HANDLER = CommandHandler("stats", stats, filters=CustomFilters.sudo_filter)
GDPR_HANDLER = CommandHandler("gdpr", gdpr, filters=Filters.private)

dispatcher.add_handler(ID_HANDLER)
dispatcher.add_handler(IP_HANDLER)
# dispatcher.add_handler(TIME_HANDLER)
dispatcher.add_handler(RUNS_HANDLER)
dispatcher.add_handler(SLAP_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(GDPR_HANDLER)
