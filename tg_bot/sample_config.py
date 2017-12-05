# Create a new config.py file in same dir and import, then extend this class.
class Config(object):
    API_KEY = "YOUR KEY HERE"
    OWNER_ID = "YOUR ID HERE"  # If you dont know, run the bot and do /id in your private chat with it
    OWNER_USERNAME = "YOUR USERNAME HERE"
    LOGGER = True
    SQLALCHEMY_DATABASE_URI = 'sqldbtype://username:pw@hostname:port/db_name'
    MESSAGE_DUMP = None


class Production(Config):
    LOGGER = False


class Development(Config):
    LOGGER = True
