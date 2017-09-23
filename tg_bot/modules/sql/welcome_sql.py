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
    with INSERTION_LOCK:
        curr = KEYSTORE.get(str(chat_id))
        if not curr:
            print("Perms didnt exist for {}! Creating.".format(chat_id))
            curr = Welcome(str(chat_id), should_welcome)
        else:
            curr.should_welcome = should_welcome
        KEYSTORE[str(chat_id)] = curr

        SESSION.add(curr)
        SESSION.commit()


def load_ks():
    all_perms = SESSION.query(Welcome).all()
    for chat in all_perms:
        KEYSTORE[chat.chat_id] = chat
    SESSION.close()
    print("Welcome message settings keystore loaded, with size {}.".format(len(KEYSTORE)))


def migrate_chat(old_chat_id, new_chat_id):
    global KEYSTORE
    with INSERTION_LOCK:
        chat = SESSION.query(Welcome).get(str(old_chat_id))
        if chat:
            chat.chat_id = str(new_chat_id)
        SESSION.commit()
        KEYSTORE = {}
        load_ks()


# LOAD KEYSTORE ON BOT START
load_ks()
