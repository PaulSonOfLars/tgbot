from tg_bot.models import MutedUsers
from tg_bot.modules.sql import session


# TODO: keystore
def is_user_muted(chat_id, user_id):
    status = session.query(MutedUsers).get(str(chat_id))
    if status:
        return user_id in status.muted_users
    else:
        return False


def mute_user(chat_id, user_id):
    status = session.query(MutedUsers).get(str(chat_id))
    if not status:
        status = MutedUsers(str(chat_id))
        session.add(status)

    status.muted_users.append(user_id)
    session.commit()


# NOTE: track user data to get ids from usernames?
def unmute_user(chat_id, user_id):
    status = session.query(MutedUsers).get(str(chat_id))
    if not status:
        status = MutedUsers(str(chat_id))
        session.add(status)

    status.muted_users.remove(user_id)
    session.commit()
