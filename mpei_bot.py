import config
import telebot
from telebot import types
from db import SQLightHelper
from parse import MPEIParser
from users import *

bot = telebot.TeleBot(config.token)
user_step = {}  # to process 2-step actions


@bot.message_handler(commands=['start'])
def send_welcome(message):
    db = SQLightHelper(config.database)
    if not db.select_single(message.chat.id):  # no user in database
        bot.send_message(message.chat.id, "Вас приветствует mpei_bot! Для начала введите вашу группу в формате X-XX-XX. (Например А-08м-17)")
        user_step[message.chat.id] = 'init_group_1'  # waiting for group name
    else:
        bot.send_message(message.chat.id, "Бот уже запущен!")
    db.close()


@bot.message_handler(commands=['schedule'])
def send_schedule(message):
    if not (message.chat.id in user_step) or user_step[message.chat.id] == 0:
        if check_user_group(message.chat.id):         
            keyboard=types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(*[types.KeyboardButton(day_of_week) for day_of_week in ['1','2','3','4','5','6']])
            bot.send_message(message.chat.id, "Введите день недели (число от 1 до 6)", reply_markup=keyboard)
            user_step[message.chat.id] = 'schedule_1'
        else:
            bot.send_message(message.chat.id, "Сначала введите группу!")


@bot.message_handler(content_types=['text'])
def messages_handler(message):
    chat_id = message.chat.id
    if chat_id in user_step:
        if user_step[chat_id] == 'schedule_1':  # return schedule by day
            user_step[chat_id] = 'schedule_2'
            bot.send_chat_action(chat_id, 'typing')
            parser = MPEIParser(config.phantom_driver_path)
            db = SQLightHelper(config.database)
            response = parser.get_by_day(db, check_user_group(chat_id), int(message.text), week=1)
            bot.send_message(message.chat.id, response)

            response = parser.get_by_day(db, check_user_group(chat_id), int(message.text), week=2)
            bot.send_message(message.chat.id, response)
            db.close()
            user_step[chat_id] = 0
        elif user_step[chat_id] == 'init_group_1':  # save user group
            db = SQLightHelper(config.database)
            db.save_user(message.chat.id, message.text)
            bot.send_message(message.chat.id, "Группа сохранена! Теперь можно получить свое расписание.")
            user_step[chat_id] = 0
        else:
            bot.send_message(message.chat.id, "Неизвестная команда")
    else:
        bot.send_message(message.chat.id, "Неизвестная команда")


if __name__ == '__main__':
    bot.polling(none_stop=True)
