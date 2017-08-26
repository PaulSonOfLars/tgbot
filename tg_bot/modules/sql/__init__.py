import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tg_bot import HEROKU
from tg_bot.models import BASE

if not HEROKU:
    from tg_bot.config import Development as Configuration


def start():
    if HEROKU:
        db_uri = os.environ.get('DATABASE_URL')
    else:
        db_uri = Configuration.SQLALCHEMY_DATABASE_URI
    engine = create_engine(db_uri)
    BASE.metadata.create_all(engine)
    session_maker = sessionmaker(autoflush=False)
    return session_maker(bind=engine)

SESSION = start()
