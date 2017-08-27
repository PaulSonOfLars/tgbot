from tg_bot.models import Welcome
from tg_bot.modules.sql import SESSION

KEYSTORE = {}


def get_preference(chat_id):
    if str(chat_id) in KEYSTORE:
        return KEYSTORE.get(str(chat_id)).should_welcome
    else:
        # Welcome by default.
        return True


def set_preference(chat_id, should_welcome):
    curr = KEYSTORE.get(str(chat_id))
    if not curr:
        print("Perms didnt exist for {}! creating".format(chat_id))
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
    print("Welcome message keystore loaded, length " + str(len(KEYSTORE)))

# LOAD KEYSTORE ON BOT START
load_ks()
