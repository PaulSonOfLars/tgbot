import html
from io import BytesIO
from typing import Optional, List

from telegram import Message, Update, Bot, User, Chat, ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

import tg_bot.modules.sql.global_bans_sql as sql
from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, STRICT_GBAN
from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import send_to_list
from tg_bot.modules.sql.users_sql import get_all_chats

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat",
}

UNGBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Method is available for supergroup and channel chats only",
    "Not in the chat",
    "Channel_private",
    "Chat_admin_required",
    "Peer_id_invalid",
}


@run_async
def gban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Non ti stai riferendo ad un utente.")
        return

    if int(user_id) in SUDO_USERS:
        message.reply_text(
            "Vi spio.. con i miei piccoli occhi.. una guarra tra sudo user! Perchè state cercando di bannarvi a vicenda?"
        )
        return

    if int(user_id) in SUPPORT_USERS:
        message.reply_text(
            "OOOH qualcuno sta cercando di effettuare un gban ad un support user! *grabs popcorn*"
        )
        return

    if user_id == bot.id:
        message.reply_text("-_- Divertente, ora mi auto gban, no? Complimenti.")
        return

    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        message.reply_text(excp.message)
        return

    if user_chat.type != "private":
        message.reply_text("Questo non è un utente!")
        return

    if sql.is_user_gbanned(user_id):
        if not reason:
            message.reply_text(
                "Questo utente è gia in gban. Cambierei il motivo se solo me ne avessi dato uno.."
            )
            return

        old_reason = sql.update_gban_reason(
            user_id, user_chat.username or user_chat.first_name, reason
        )
        if old_reason:
            message.reply_text(
                "Questo utente è già in gban, per la seguente ragione:\n"
                "<code>{}</code>\n"
                "Ho aggiornato il mio sistema con la nuova motivazione!".format(
                    html.escape(old_reason)
                ),
                parse_mode=ParseMode.HTML,
            )
        else:
            message.reply_text(
                "Questo utente è già in gban, ma senza ragione. Ho appena aggiornato i miei sistemi!"
            )

        return

    message.reply_text("*Blows dust off of banhammer* 😉")

    banner = update.effective_user  # type: Optional[User]
    send_to_list(
        bot,
        SUDO_USERS + SUPPORT_USERS,
        "{} sta effettuando un gban all'utente {} "
        "per il seguente motivo:\n{}".format(
            mention_html(banner.id, banner.first_name),
            mention_html(user_chat.id, user_chat.first_name),
            reason or "senza una ragione specifica.",
        ),
        html=True,
    )

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            bot.kick_chat_member(chat_id, user_id)
        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                message.reply_text(
                    "Non posso gbannare per il seguente motivo: {}".format(excp.message)
                )
                send_to_list(
                    bot,
                    SUDO_USERS + SUPPORT_USERS,
                    "Non posso gbannare per il seguente motivo: {}".format(
                        excp.message
                    ),
                )
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "gban completato!")
    message.reply_text("Utente gbannato!")


@run_async
def ungban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("A quanto pare non ti stai riferendo ad utente.")
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != "private":
        message.reply_text("Questo non è un utente!")
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text("Questo utente non è gbannato!")
        return

    banner = update.effective_user  # type: Optional[User]

    message.reply_text(
        "Darò a  {} una seconda chance, globalmente.".format(user_chat.first_name)
    )

    send_to_list(
        bot,
        SUDO_USERS + SUPPORT_USERS,
        "{} ha disabilitato il gban per l'utente {}".format(
            mention_html(banner.id, banner.first_name),
            mention_html(user_chat.id, user_chat.first_name),
        ),
        html=True,
    )

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == "kicked":
                bot.unban_chat_member(chat_id, user_id)

        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                message.reply_text(
                    "Non posso disabilitare il gban a questo utente per il seguente motivo: {}".format(
                        excp.message
                    )
                )
                bot.send_message(
                    OWNER_ID,
                    "Non posso disabilitare il gban a questo utente per il seguente motivo: {}".format(
                        excp.message
                    ),
                )
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "un-gban completo!")

    message.reply_text("L'utente è stato un-gbanned.")


@run_async
def gbanlist(bot: Bot, update: Update):
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text(
            "Non ci sono utente gbanned.. sei più gentile di quanto non mi aspettassi..."
        )
        return

    banfile = "Screw these guys.\n"
    for user in banned_users:
        banfile += "[x] {} - {}\n".format(user["name"], user["user_id"])
        if user["reason"]:
            banfile += "Reason: {}\n".format(user["reason"])

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="gbanlist.txt",
            caption="Here is the list of currently gbanned users.",
        )


def check_and_ban(update, user_id, should_message=True):
    if sql.is_user_gbanned(user_id):
        update.effective_chat.kick_member(user_id)
        if should_message:
            update.effective_message.reply_text(
                "Questo utente è malevole.. Non dovrebbe essere qui!"
            )


@run_async
def enforce_gban(bot: Bot, update: Update):
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    if (
            sql.does_chat_gban(update.effective_chat.id)
            and update.effective_chat.get_member(bot.id).can_restrict_members
    ):
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        msg = update.effective_message  # type: Optional[Message]

        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id)

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user  # type: Optional[User]
            if user and not is_user_admin(chat, user.id):
                check_and_ban(update, user.id, should_message=False)


@run_async
@user_admin
def gbanstat(bot: Bot, update: Update, args: List[str]):
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "Ho abilitato gban per questo gruppo. Ti aiuterò a proteggerti dagli "
                "spammers, personalità antipatiche, e i più grandi trolls."
            )
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "Ho disabilitato gban per questo gruppo. Attenzione: "
                "sei meno protetto dai trolls e dagli spammers!"
            )
    else:
        update.effective_message.reply_text(
            "Devi specificare un argomento! on/off, yes/no!\n\n"
            "Le impostazioni attuali sono: {}\n"
            "quando True, ogni gban che avviene, avverrà anche in questo gruppo. "
            "quando False, non verrai protetto da trolls e "
            "spammers.".format(sql.does_chat_gban(update.effective_chat.id))
        )


def __stats__():
    return "{} utenti in gban.".format(sql.num_gbanned_users())


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)

    text = "Ban globali: <b>{}</b>"
    if is_gbanned:
        text = text.format("Yes")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += "\nReason: {}".format(html.escape(user.reason))
    else:
        text = text.format("No")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "Questa chat sta utilizzando i poteri del *gban*: `{}`.".format(
        sql.does_chat_gban(chat_id)
    )


__help__ = """
*Admin only:*
 - /gbanstat <on/off/yes/no>: Disabiliterà il gban dei tuoi gruppi o visualizzerà le tue impostazioni attuali.

Gban, conosciuto anche come global ban ti aiuta a tenere il tuo gruppo pulito da spammer e trolls in automatico.
"""

__mod_name__ = "Global Bans"

GBAN_HANDLER = CommandHandler(
    "gban",
    gban,
    pass_args=True,
    filters=CustomFilters.sudo_filter | CustomFilters.support_filter,
)
UNGBAN_HANDLER = CommandHandler(
    "ungban",
    ungban,
    pass_args=True,
    filters=CustomFilters.sudo_filter | CustomFilters.support_filter,
)
GBAN_LIST = CommandHandler(
    "gbanlist",
    gbanlist,
    filters=CustomFilters.sudo_filter | CustomFilters.support_filter,
)

GBAN_STATUS = CommandHandler(
    "gbanstat", gbanstat, pass_args=True, filters=Filters.group
)

GBAN_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gban)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
