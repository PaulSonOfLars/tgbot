from telegram import Message
from telegram.ext import BaseFilter

from tg_bot import SUPPORT_USERS, SUDO_USERS
from tg_bot.modules.sql.users_sql import get_restriction


class CustomFilters(object):
    class _Supporters(BaseFilter):
        def filter(self, message: Message):
            return bool(message.from_user and message.from_user.id in SUPPORT_USERS)

    support_filter = _Supporters()

    class _Sudoers(BaseFilter):
        def filter(self, message: Message):
            return bool(message.from_user and message.from_user.id in SUDO_USERS)

    sudo_filter = _Sudoers()

    class _MimeType(BaseFilter):
        def __init__(self, mimetype):
            self.mime_type = mimetype
            self.name = "CustomFilters.mime_type({})".format(self.mime_type)

        def filter(self, message: Message):
            return bool(message.document and message.document.mime_type == self.mime_type)

    mime_type = _MimeType

    class _HasText(BaseFilter):
        def filter(self, message: Message):
            return bool(message.text or message.sticker or message.photo or message.document or message.video)

    has_text = _HasText()

    class _ChatRestricted(BaseFilter):
        def filter(self, message: Message):
            return get_restriction(message.chat.id)

    chat_restricted = _ChatRestricted()
