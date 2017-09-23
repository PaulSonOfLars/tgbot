import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

from tg_bot import HEROKU

if not HEROKU:
    from tg_bot.config import Development as Configuration


def start():
    if HEROKU:
        db_uri = os.environ.get('DATABASE_URL')
    else:
        db_uri = Configuration.SQLALCHEMY_DATABASE_URI
    engine = create_engine(db_uri, client_encoding="utf8")
    BASE.metadata.bind = engine
    BASE.metadata.create_all(engine)
    return scoped_session(sessionmaker(bind=engine, autoflush=False))


BASE = declarative_base()
SESSION = start()
