import json
from io import BytesIO
from typing import Optional

from telegram import Message, Chat, Update, Bot
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async

from tg_bot import dispatcher, LOGGER
from tg_bot.__main__ import DATA_IMPORT
from tg_bot.modules.helper_funcs.chat_status import user_admin


@run_async
@user_admin
def import_data(bot: Bot, update):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    # TODO: allow uploading doc with command, not just as reply
    # only work with a doc
    if msg.reply_to_message and msg.reply_to_message.document:
        try:
            file_info = bot.get_file(msg.reply_to_message.document.file_id)
        except BadRequest:
            msg.reply_text(
                "Prova a scaricare e ricaricare il file manualmente. "
                "Momentaneamente questa richiesta non può essere completata."
            )
            return

        with BytesIO() as file:
            file_info.download(out=file)
            file.seek(0)
            data = json.load(file)

        # only import one group
        if len(data) > 1 and str(chat.id) not in data:
            msg.reply_text(
                "Ci sono più chat nello stesso file ma nessuno ha l'id di questa chat "
                "- come posso capire cosa importare qui?"
            )
            return

        # Select data source
        if str(chat.id) in data:
            data = data[str(chat.id)]["hashes"]
        else:
            data = data[list(data.keys())[0]]["hashes"]

        try:
            for mod in DATA_IMPORT:
                mod.__import_data__(str(chat.id), data)
        except Exception:
            msg.reply_text(
                "Un eccezione è avvenuto mentre provavo a ripristinare i messaggi. Il processo potrebbe non essere completo. Se"
                "hai problemi con il file ti consiglio di inviarlo al gruppo admin e in modo da debuggarlo. "
                "I report su github sono molto apprezzati! Grazie! :)"
            )
            LOGGER.exception(
                "Import for chatid %s with name %s failed.",
                str(chat.id),
                str(chat.title),
            )
            return

        # TODO: some of that link logic
        # NOTE: consider default permissions stuff?
        msg.reply_text("Backup ricaricato! Ben tornati!")


@run_async
@user_admin
def export_data(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    msg.reply_text("")


__mod_name__ = "Backups"

__help__ = """
*Admin only:*
 - /import: Rispondi con un file di backup per ricaricare tutte le chat! Attenzione \
i file e le foto non posso essere importati a causa delle restrizioni di Telegram.
 - /export: !!! Questo comando non è ancora disponibile. L'exoport deve essere effettuato manualmente dal db!
"""
IMPORT_HANDLER = CommandHandler("import", import_data)
EXPORT_HANDLER = CommandHandler("export", export_data)

dispatcher.add_handler(IMPORT_HANDLER)
# dispatcher.add_handler(EXPORT_HANDLER)
