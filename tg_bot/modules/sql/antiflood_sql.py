import threading

from sqlalchemy import Column, BigInteger, String

from tg_bot.modules.sql import BASE, SESSION

DEF_COUNT = 0
DEF_LIMIT = 0


class FloodControl(BASE):
    __tablename__ = "antiflood"
    chat_id = Column(String(14), primary_key=True)
    count = Column(BigInteger, default=DEF_COUNT)
    limit = Column(BigInteger, default=DEF_LIMIT)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)  # ensure string

    def __repr__(self):
        return "<flood control for %s>" % self.chat_id


FloodControl.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()

CHAT_FLOOD = {}


def set_flood(chat_id, amount):
    with INSERTION_LOCK:
        flood = SESSION.query(FloodControl).get(str(chat_id))
        if not flood:
            flood = FloodControl(str(chat_id))
        flood.limit = amount
        CHAT_FLOOD[str(chat_id)] = (None, None, DEF_COUNT, amount)
        SESSION.add(flood)
        SESSION.commit()


def update_flood(chat_id: str, user_id, is_channel) -> bool:
    if str(chat_id) in CHAT_FLOOD:
        curr_user_id, curr_is_channel, count, limit = CHAT_FLOOD[str(chat_id)]
        if limit == 0:
            return False
        if (user_id != curr_user_id and is_channel != curr_is_channel) or user_id is None:  # other user
            CHAT_FLOOD[str(chat_id)] = (user_id, is_channel, DEF_COUNT + 1, limit)
            return False
        count += 1
        if count > limit:  # too many msgs, kick
            CHAT_FLOOD[str(chat_id)] = (None, None, DEF_COUNT, limit)
            return True
        # default -> update
        CHAT_FLOOD[str(chat_id)] = (user_id, is_channel, count, limit)
        return False


def get_flood_limit(chat_id):
    return CHAT_FLOOD[str(chat_id)][2]


def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        flood = SESSION.query(FloodControl).get(str(old_chat_id))
        if flood:
            CHAT_FLOOD[str(new_chat_id)] = CHAT_FLOOD[str(old_chat_id)]
            flood.chat_id = str(new_chat_id)
            SESSION.commit()
        SESSION.close()


def __load_flood_settings():
    global CHAT_FLOOD
    try:
        all_chats = SESSION.query(FloodControl).all()
        CHAT_FLOOD = {chat.chat_id: (None, None, DEF_COUNT, chat.limit) for chat in all_chats}
    finally:
        SESSION.close()


__load_flood_settings()
