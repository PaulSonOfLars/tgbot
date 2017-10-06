# Note: chat_id's are stored as strings because the int is too large to be stored in a PSQL database.
import threading

from sqlalchemy import Column, String, Boolean, UnicodeText

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

INSERTION_LOCK = threading.Lock()


def add_note_to_db(chat_id, notename, note_data, is_reply=False):
    with INSERTION_LOCK:
        prev = SESSION.query(Notes).get((str(chat_id), notename))
        if prev:
            SESSION.delete(prev)
        note = Notes(str(chat_id), notename, note_data, is_reply=is_reply)

        SESSION.add(note)
        SESSION.commit()


def get_note(chat_id, notename):
    return SESSION.query(Notes).get((str(chat_id), notename))


def rm_note(chat_id, notename):
    with INSERTION_LOCK:
        note = SESSION.query(Notes).get((str(chat_id), notename))
        if note:
            SESSION.delete(note)
            SESSION.commit()
            return True
        else:
            return False


def get_all_chat_notes(chat_id):
    return SESSION.query(Notes).filter(Notes.chat_id == str(chat_id)).all()


def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat_notes = SESSION.query(Notes).filter(Notes.chat_id == str(old_chat_id)).all()
        for note in chat_notes:
            note.chat_id = str(new_chat_id)
        SESSION.commit()
