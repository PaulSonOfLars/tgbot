# Note: chat_id's are stored as strings because the int is too large to be stored in a PSQL database.
from tg_bot.models import Notes
from tg_bot.modules.sql import session


def add_note_to_db(chat_id, notename, note_data, is_reply=False):
    prev = session.query(Notes).get((str(chat_id), notename))
    if prev:
        session.delete(prev)
    note = Notes(str(chat_id), notename, note_data, is_reply=is_reply)
    session.add(note)
    session.commit()


def get_note(chat_id, notename):
    return session.query(Notes).get((str(chat_id), notename))


def rm_note(chat_id, notename):
    note = session.query(Notes).get((str(chat_id), notename))
    if note:
        session.delete(note)
        session.commit()


def get_all_chat_notes(chat_id):
    return session.query(Notes).filter(Notes.chat_id == str(chat_id)).all()
