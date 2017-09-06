# Note: chat_id's are stored as strings because the int is too large to be stored in a PSQL database.
from sqlalchemy import Column, String, Boolean, UnicodeText
from sqlalchemy.exc import IntegrityError

from tg_bot.modules.sql import SESSION, BASE


class Notes(BASE):
    __tablename__ = "notes"
    chat_id = Column(String(14), primary_key=True)
    name = Column(UnicodeText, primary_key=True)
    value = Column(UnicodeText, nullable=False)
    is_reply = Column(Boolean, default=False)

    def __init__(self, chat_id, name, value, is_reply=False):
        self.chat_id = str(chat_id)  # ensure string
        self.name = name
        self.value = value
        self.is_reply = is_reply

    def __repr__(self):
        return "<Note %s>" % self.name

Notes.__table__.create(checkfirst=True)


def add_note_to_db(chat_id, notename, note_data, is_reply=False):
    prev = SESSION.query(Notes).get((str(chat_id), notename))
    if prev:
        SESSION.delete(prev)
    note = Notes(str(chat_id), notename, note_data, is_reply=is_reply)
    SESSION.add(note)
    try:
        SESSION.commit()
    except IntegrityError:
        SESSION.rollback()


def get_note(chat_id, notename):
    return SESSION.query(Notes).get((str(chat_id), notename))


def rm_note(chat_id, notename):
    note = SESSION.query(Notes).get((str(chat_id), notename))
    if note:
        SESSION.delete(note)
        try:
            SESSION.commit()
        except IntegrityError:
            SESSION.rollback()


def get_all_chat_notes(chat_id):
    return SESSION.query(Notes).filter(Notes.chat_id == str(chat_id)).all()
