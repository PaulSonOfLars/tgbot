import threading

from sqlalchemy import String, Column, Integer

from tg_bot.modules.sql import SESSION, BASE


class FloodControl(BASE):
    __tablename__ = "antiflood"
    chat_id = Column(String(14), primary_key=True)
    user_id = Column(Integer)
    count = Column(Integer, default=0)
    limit = Column(Integer, default=0)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)  # ensure string

    def __repr__(self):
        return "<flood control for %s>" % self.chat_id


FloodControl.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()


def set_flood(chat_id, amount):
    with INSERTION_LOCK:
        flood = SESSION.query(FloodControl).get(str(chat_id))
        if not flood:
            flood = FloodControl(str(chat_id))

        flood.user_id = None
        flood.limit = amount

        SESSION.add(flood)
        SESSION.commit()


def update_flood(chat_id, user_id):
    with INSERTION_LOCK:
        flood = SESSION.query(FloodControl).get(str(chat_id))

        if flood and flood.limit != 0:
            if flood.user_id != user_id:
                flood.user_id = user_id
                flood.count = 0

            if not user_id:
                SESSION.commit()
                return False

            flood.count += 1

            if flood.count > flood.limit:
                flood.user_id = None
                flood.count = 0

                SESSION.commit()
                return True

            SESSION.commit()
            return False

        SESSION.close()
        return False


def get_flood(chat_id):
    try:
        return SESSION.query(FloodControl).get(str(chat_id))
    finally:
        SESSION.close()


def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        flood = SESSION.query(FloodControl).get(str(old_chat_id))
        if flood:
            flood.chat_id = str(new_chat_id)
            SESSION.commit()

        SESSION.close()
