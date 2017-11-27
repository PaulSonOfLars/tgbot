import threading

from sqlalchemy import Integer, Column, String, UnicodeText
from sqlalchemy.dialects import postgresql

from tg_bot.modules.sql import SESSION, BASE


class Warns(BASE):
    __tablename__ = "warns"

    user_id = Column(Integer, primary_key=True)
    chat_id = Column(String(14), primary_key=True)
    num_warns = Column(Integer, default=0)
    reasons = Column(postgresql.Array(UnicodeText))

    def __init__(self, user_id, chat_id):
        self.user_id = user_id
        self.chat_id = str(chat_id)

    def __repr__(self):
        return "<{} warns for {} in {}>".format(self.num_warns, self.user_id, self.chat_id)


Warns.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.Lock()


def warn_user(user_id, chat_id, reason):
    with INSERTION_LOCK:
        warned_user = SESSION.query(Warns).get(user_id, str(chat_id))
        if not warned_user:
            warned_user = Warns(user_id, str(chat_id))

        warned_user.num_warns += 1
        warned_user.reasons.append(reason)

        SESSION.add(warned_user)
        SESSION.commit()

        return warned_user


def reset_warns(user_id, chat_id):
    with INSERTION_LOCK:
        warned_user = SESSION.query(Warns).get(user_id, str(chat_id))

        warned_user.num_warns = 0
        warned_user.reasons = []

        SESSION.add(warned_user)
        SESSION.commit()


def get_warns(user_id, chat_id):
    return SESSION.query(Warns).get(user_id, str(chat_id))
