from tg_bot.models import UserInfo
from tg_bot.modules.sql import session


def get_user_info(user_id):
    userinfo = session.query(UserInfo).get(user_id)
    if userinfo:
        return userinfo.info
    return None


def set_user_info(user_id, info):
    userinfo = session.query(UserInfo).get(user_id)
    if userinfo:
        userinfo.info = info
    else:
        userinfo = UserInfo(user_id, info)
    session.add(userinfo)
    session.commit()
