import threading

from sqlalchemy import Integer, Column, String, UnicodeText
from sqlalchemy.dialects import postgresql

from tg_bot.modules.sql import SESSION, BASE


class Warns(BASE):
    __tablename__ = "warns"

    user_id = Column(Integer, primary_key=True)
    chat_id = Column(String(14), primary_key=True)
    num_warns = Column(Integer, default=0)
    reasons = Column(postgresql.ARRAY(UnicodeText))

    def __init__(self, user_id, chat_id):
        self.user_id = user_id
        self.chat_id = str(chat_id)
        self.num_warns = 0
        self.reasons = []

    def __repr__(self):
        return "<{} warns for {} in {} for reasons {}>".format(self.num_warns, self.user_id, self.chat_id, self.reasons)


Warns.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.Lock()


def warn_user(user_id, chat_id, reason=None):
    with INSERTION_LOCK:
        warned_user = SESSION.query(Warns).get((user_id, str(chat_id)))
        if not warned_user:
            warned_user = Warns(user_id, str(chat_id))

        warned_user.num_warns += 1
        if reason:
            warned_user.reasons = warned_user.reasons + [reason]  # TODO:: double check this wizardry

        SESSION.add(warned_user)
        SESSION.commit()

        return warned_user


def reset_warns(user_id, chat_id):
    with INSERTION_LOCK:
        warned_user = SESSION.query(Warns).get((user_id, str(chat_id)))

        warned_user.num_warns = 0
        warned_user.reasons = []

        SESSION.add(warned_user)
        SESSION.commit()


def get_warns(user_id, chat_id):
    return SESSION.query(Warns).get((user_id, str(chat_id)))


def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat_notes = SESSION.query(Warns).filter(Warns.chat_id == str(old_chat_id)).all()
        for note in chat_notes:
            note.chat_id = str(new_chat_id)
        SESSION.commit()
