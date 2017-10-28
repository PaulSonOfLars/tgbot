import threading

from sqlalchemy import Column, String, Boolean, UnicodeText

from tg_bot.modules.sql import SESSION, BASE


class Welcome(BASE):
    __tablename__ = "welcome_pref"
    chat_id = Column(String(14), primary_key=True)
    should_welcome = Column(Boolean, default=True)
    custom_welcome = Column(UnicodeText, default="")
    custom_leave = Column(UnicodeText, default="")

    def __init__(self, chat_id, should_welcome=True):
        self.chat_id = chat_id
        self.should_welcome = should_welcome

    def __repr__(self):
        return "<Chat {} should Welcome new users: {}>".format(self.chat_id, self.should_welcome)


Welcome.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.Lock()


def get_preference(chat_id):
    welc = SESSION.query(Welcome).get(str(chat_id))
    if welc:
        return welc.should_welcome, welc.custom_welcome, welc.custom_leave
    else:
        # Welcome by default.
        return True, "", ""


def set_preference(chat_id, should_welcome):
    with INSERTION_LOCK:
        curr = SESSION.query(Welcome).get(str(chat_id))
        if not curr:
            curr = Welcome(str(chat_id), should_welcome)
        else:
            curr.should_welcome = should_welcome

        SESSION.add(curr)
        SESSION.commit()


def set_custom_welcome(chat_id, custom_welcome):
    with INSERTION_LOCK:
        welcome_settings = SESSION.query(Welcome).get(str(chat_id))
        if not welcome_settings:
            welcome_settings = Welcome(str(chat_id), True)
        welcome_settings.custom_welcome = custom_welcome

        SESSION.add(welcome_settings)
        SESSION.commit()


def get_custom_welcome(chat_id):
    welcome_settings = SESSION.query(Welcome).get(str(chat_id))
    ret = ""
    if welcome_settings and welcome_settings.custom_welcome:
        ret = welcome_settings.custom_welcome

    SESSION.close()
    return ret


def set_custom_leave(chat_id, custom_leave):
    with INSERTION_LOCK:
        welcome_settings = SESSION.query(Welcome).get(str(chat_id))
        if not welcome_settings:
            welcome_settings = Welcome(str(chat_id), True)
        welcome_settings.custom_leave = custom_leave

        SESSION.add(welcome_settings)
        SESSION.commit()


def get_custom_leave(chat_id):
    welcome_settings = SESSION.query(Welcome).get(str(chat_id))
    ret = ""
    if welcome_settings and welcome_settings.custom_leave:
        ret = welcome_settings.custom_leave

    SESSION.close()
    return ret


def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat = SESSION.query(Welcome).get(str(old_chat_id))
        if chat:
            chat.chat_id = str(new_chat_id)
        SESSION.commit()
