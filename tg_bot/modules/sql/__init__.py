import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tg_bot import HEROKU
if not HEROKU:
    from tg_bot.config import Development as Configuration
from tg_bot.models import Base


def start():
    if HEROKU:
        db_uri = os.environ.get('DATABASE_URL')
    else:
        db_uri = Configuration.SQLALCHEMY_DATABASE_URI
    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)
    session_maker = sessionmaker(autoflush=False)
    return session_maker(bind=engine)

session = start()
