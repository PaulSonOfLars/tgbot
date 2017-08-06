# Note: chat_id's are stored as strings because the int is over 32 bits.
from tg_bot.models import Notes
from tg_bot.modules.sql import session


def add_note_to_db(chat_id, notename, note_data):
    prev = session.query(Notes).get((str(chat_id), notename))
    if prev:
        prev.value = note_data
        note = prev
    else:
        note = Notes(str(chat_id), notename, note_data)
    session.add(note)
    session.commit()


def get_note(chat_id, notename):
    return session.query(Notes).get((str(chat_id), notename))


def rm_note(chat_id, notename):
    note = session.query(Notes).get((str(chat_id), notename))
    if note:
        session.delete(note)
        session.commit()
