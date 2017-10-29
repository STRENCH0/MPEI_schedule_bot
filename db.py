import sqlite3


class SQLightHelper:
    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def select_all(self):
        """ Получаем все строки """
        with self.connection:
            return self.cursor.execute('select * from chats').fetchall()

    def select_single(self, chat_id):
        """ Получаем одну строку с номером rownum """
        with self.connection:
            return self.cursor.execute('SELECT * FROM chats WHERE chat_id = ?', (chat_id,)).fetchall()

    def save_user(self, chat_id, group):
        with self.connection:
            self.cursor.execute("INSERT INTO chats(chat_id, 'group') VALUES (?, ?)", (chat_id, group))

    def save_group(self, group, chat_id):
        with self.connection:
            self.cursor.execute("UPDATE chats SET 'group' = ? WHERE chat_id = ?", (group, chat_id))

    def close(self):
        """ Закрываем текущее соединение с БД """
        self.connection.close()