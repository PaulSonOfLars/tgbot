from telegram.ext import BaseFilter

from tg_bot import SUPPORT_USERS, SUDO_USERS


class CustomFilters(object):
    class _Supporters(BaseFilter):
        def filter(self, message):
            return bool(message.from_user and message.from_user.id in SUPPORT_USERS)

    support_filter = _Supporters()

    class _Sudoers(BaseFilter):
        def filter(self, message):
            return bool(message.from_user and message.from_user.id in SUDO_USERS)

    sudo_filter = _Sudoers()

    class _MimeType(BaseFilter):
        def __init__(self, mimetype):
            self.mime_type = mimetype
            self.name = "CustomFilters.mime_type({})".format(self.mime_type)

        def filter(self, message):
            return bool(message.document and message.document.mime_type == self.mime_type)

    mime_type = _MimeType
