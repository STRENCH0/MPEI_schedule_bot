import time

from db import SQLightHelper
import config


users = {}


class UserSpec:
    def __init__(self, group):
        self.group = group
        self.last_used = time.time()


def check_user_group(chat_id):
    if chat_id in users:
        users[chat_id].last_used = time.time()
        return users[chat_id].group
    else:
        database = SQLightHelper(config.database)
        user = database.select_single(chat_id)
        if not user:
            return False
        user_group = user[0][1]
        user_spec = UserSpec(user_group)
        if len(users) > 20:            # cleaning dictionary
            for i in users:
                if time.time() - users[i].last_used > config.timeout_to_clear_buffer:
                    users.pop(i)

        users[user[0][0]] = user_spec
        return user_group


def delete_user(chat_id):
    db = SQLightHelper(config.database)
    if chat_id in users:
        users.pop(chat_id)
    if db.delete_user(chat_id):
        db.close()
        return True
    else:
        db.close()
        return False
