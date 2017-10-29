import sqlite3
import config
from schedule import Lesson


class SQLightHelper:
    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()
        self.group_id = None

    def select_all(self):
        with self.connection:
            return self.cursor.execute(
                'SELECT chats.chat_id, groups.group_name FROM chats, groups WHERE chats.group_id = groups.group_id').fetchall()

    def select_single(self, chat_id):
        with self.connection:
            return self.cursor.execute(
                'SELECT chats.chat_id, groups.group_name  FROM chats, groups WHERE chat_id = ? AND'
                ' groups.group_id = chats.group_id', (chat_id,)).fetchall()

    def save_user(self, chat_id, group):
        with self.connection:
            try:
                group_id = self.select_group_id(group)
                if not group_id:
                    self.cursor.execute("INSERT INTO groups(group_name) VALUES (?)", (group.upper(),))
                    group_id = self.cursor.execute("SELECT group_id FROM groups WHERE group_name = ?",
                                                   (group.upper(),)).fetchall()[0][0]
                self.cursor.execute("INSERT INTO chats(chat_id, group_id) VALUES (?, ?)", (chat_id, group_id))
                return True
            except Exception:
                return False

    def save_lesson(self, day, week, lesson, group_id, number):
        with self.connection:
            self.cursor.execute(
                'INSERT INTO schedule(day, week, lesson, group_id, number) VALUES (?, ?, ?, ?, ?)',
                (day, week, lesson, group_id, number))
            return True

    def select_group_id(self, group_name):
        if self.group_id is None:
            group_id_exec = self.cursor.execute("SELECT group_id FROM groups WHERE group_name = ?",
                                                (group_name.upper(),)).fetchall()
            if not group_id_exec:
                return False
            else:
                group_id = group_id_exec[0][0]
                return group_id
        else:
            return self.group_id

    def select_lesson_id(self, group_id, day, week, number):
        lesson_id_exec = self.cursor.execute(
            "SELECT lesson_id FROM schedule WHERE  group_id = ? AND day = ? AND week = ? AND number = ?",
            (group_id, day, week, number)).fetchall()
        if not lesson_id_exec:
            return False
        else:
            return lesson_id_exec[0][0]

    def select_lessons_by_day(self, group_id, week, day, name_only=True):
        if name_only:
            lessons = self.cursor.execute(
                "SELECT number, lesson FROM schedule WHERE  group_id = ? AND day = ? AND week = ? ORDER BY number ASC",
                (group_id, day, week)).fetchall()
            if not lessons:
                return False
            lessons_exec = ['-----', '-----', '-----', '-----', '-----']
            for lesson in lessons:
                lessons_exec[lesson[0] - 1] = lesson[1]
            return lessons_exec
        else:
            return self.cursor.execute(
                "SELECT * FROM schedule WHERE  group_id = ? AND day = ? AND week = ? ORDER BY number ASC",
                (group_id, day, week)).fetchall()

    def delete_lessons(self, group):
        group_id = self.select_group_id(group)
        if group_id:
            self.cursor.execute("DELETE FROM schedule WHERE group_id = ?", (group_id,))
            return True
        else:
            return False

    def close(self):
        self.connection.close()


# db = SQLightHelper(config.database)
# if db.select_lessons_by_day(4, 1, 2):
#     print(True)
# db.close()