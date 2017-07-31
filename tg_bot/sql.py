from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tg_bot.models import Base, Notes
from tg_bot.config import Development as Configuration

engine = create_engine(Configuration.SQLALCHEMY_DATABASE_URI)

Base.metadata.create_all(engine)

Session = sessionmaker(autoflush=False)
sess = Session(bind=engine)


# Note: chat_id's are stored as strings because the int is over 32 bits.
def add_note_to_db(chat_id, notename, note_data):
    prev = sess.query(Notes).get((str(chat_id), notename))
    if prev:
        prev.value = note_data
        note = prev
    else:
        note = Notes(str(chat_id), notename, note_data)
    sess.add(note)
    sess.commit()


def get_note(chat_id, notename):
    return sess.query(Notes).get((str(chat_id), notename))


def rm_note(chat_id, notename):
    note = sess.query(Notes).get((str(chat_id), notename))
    sess.delete(note)
    sess.commit()
