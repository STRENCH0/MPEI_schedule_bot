import config
import telebot
from telebot import types
from db import SQLightHelper
from parse import MPEIParser
from users import *

bot = telebot.TeleBot(config.token)
user_step = {}  # to process 2-step actions
days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']


@bot.message_handler(commands=['start'])
def send_welcome(message):
    db = SQLightHelper(config.database)
    user = db.select_single(message.chat.id)
    if not user:  # no user or his group in database
        bot.send_message(message.chat.id,
                         "Вас приветствует mpei_bot! Для начала введите вашу группу в формате X-XX-XX. (Например А-07м-17)")
        user_step[message.chat.id] = 'init_group_1'  # waiting for group name
    else:
        bot.send_message(message.chat.id, "Бот уже запущен!")
    db.close()


@bot.message_handler(commands=['schedule'])
def send_schedule(message):
    if not (message.chat.id in user_step) or user_step[message.chat.id] == 0:
        if check_user_group(message.chat.id):
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(*[types.KeyboardButton(day_of_week) for day_of_week in days])
            bot.send_message(message.chat.id, "Введите день недели", reply_markup=keyboard)
            user_step[message.chat.id] = 'schedule_1'
        else:
            bot.send_message(message.chat.id, "Сначала введите группу!")


@bot.message_handler(commands=['delete_group'])
def delete_group(message):
    if not (message.chat.id in user_step) or user_step[message.chat.id] == 0:
        if delete_user(message.chat.id):
            bot.send_message(message.chat.id, "Группа удалена")
        else:
            bot.send_message(message.chat.id, "Команда недоступна")
    else:
        bot.send_message(message.chat.id, "Команда недоступна")


@bot.message_handler(content_types=['text'])
def messages_handler(message):
    chat_id = message.chat.id
    if chat_id in user_step:
        if user_step[chat_id] == 'schedule_1':  # return schedule by day
            user_step[chat_id] = 'schedule_2'
            bot.send_chat_action(chat_id, 'typing')
            parser = MPEIParser(config.phantom_driver_path)
            db = SQLightHelper(config.database)
            hide_board = types.ReplyKeyboardRemove()
            response = parser.get_by_day(db, check_user_group(chat_id), days.index(message.text) + 1, week=1)
            if not response:
                bot.send_message(message.chat.id, 'Расписание не найдено!', reply_markup=hide_board)
            else:
                bot.send_message(message.chat.id, response, reply_markup=hide_board)
                response = parser.get_by_day(db, check_user_group(chat_id), days.index(message.text) + 1, week=2)
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
