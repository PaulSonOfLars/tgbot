import threading

from sqlalchemy import Column, String, Boolean

from tg_bot.modules.sql import SESSION, BASE


class Welcome(BASE):
    __tablename__ = "welcome_pref"
    chat_id = Column(String(14), primary_key=True)
    should_welcome = Column(Boolean, default=True)

    def __init__(self, chat_id, should_welcome=True):
        self.chat_id = chat_id
        self.should_welcome = should_welcome

    def __repr__(self):
        return "<Chat {} should Welcome new users: {}>".format(self.chat_id, self.should_welcome)

Welcome.__table__.create(checkfirst=True)

KEYSTORE = {}

INSERTION_LOCK = threading.Lock()


def get_preference(chat_id):
    if str(chat_id) in KEYSTORE:
        return KEYSTORE.get(str(chat_id)).should_welcome
    else:
        # Welcome by default.
        return True


def set_preference(chat_id, should_welcome):
    INSERTION_LOCK.acquire()
    curr = KEYSTORE.get(str(chat_id))
    if not curr:
        print("Perms didnt exist for {}! creating".format(chat_id))
        curr = Welcome(str(chat_id), should_welcome)
    else:
        curr.should_welcome = should_welcome
    KEYSTORE[str(chat_id)] = curr

    SESSION.add(curr)
    SESSION.commit()
    INSERTION_LOCK.release()


def load_ks():
    all_perms = SESSION.query(Welcome).all()
    for chat in all_perms:
        KEYSTORE[chat.chat_id] = chat
    print("Welcome message keystore loaded, length " + str(len(KEYSTORE)))

# LOAD KEYSTORE ON BOT START
load_ks()
