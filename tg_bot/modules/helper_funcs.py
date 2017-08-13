# TODO make some helper module for these or something idk
def can_delete(chat, bot_id):
    return chat.get_member(bot_id).can_delete_messages


def is_user_admin(chat, user_id):
    return chat.get_member(user_id).status == 'administrator'


def is_bot_admin(chat, bot_id):
    return chat.get_member(bot_id).status == 'administrator'
