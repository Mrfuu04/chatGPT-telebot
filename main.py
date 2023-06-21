import logging
import os

import strings
import telebot
from database import (
    database,
)
from dotenv import (
    load_dotenv,
)
from gpt import (
    ChatGPT,
)
from telebot import (
    types,
)


def init_loger():
    logging.basicConfig(
        level=logging.INFO,
        filename=os.path.join(os.getcwd(), 'logs.log'),
        format="%(asctime)s %(levelname)s %(message)s",
        encoding='utf-8',
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    console_handler.setFormatter(console_formatter)

    logger = logging.getLogger()
    logger.addHandler(console_handler)


load_dotenv()
init_loger()

bot = telebot.TeleBot(os.getenv('TELEGRAM_API'))
chatGPT = ChatGPT()


def create_updated_markup(button_text, callback_data=None):
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(button_text, callback_data=callback_data)
    markup.add(button)

    return markup


def add_buttons_to_keyboard(keyboard, buttons):
    for btn_name in buttons:
        btn = types.KeyboardButton(btn_name)
        keyboard.add(btn)


@bot.message_handler(commands=['start'])
def start(message):
    logging.info(f'Пользователь {message.from_user.username} использовал /start')
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    add_buttons_to_keyboard(keyboard, ['Функции', 'О боте'])

    bot.send_message(message.chat.id, strings.START_MESSAGE, reply_markup=keyboard)


@bot.message_handler(commands=[strings.SET_SYSTEM_ROLE[1:]])
def set_system_role(message):
    if message.text == strings.SET_SYSTEM_ROLE:
        answer = 'Вы ничего не ввели'
    else:
        message_splited = ' '.join(message.text.split()[1:])

        logging.info(f'Пользователь {message.from_user.username} задал роль {message_splited}')

        database.set_new_role(message.from_user.id, message_splited)
        answer = chatGPT.ask_gpt(message)

    bot.send_message(message.chat.id, answer)


@bot.message_handler(func=lambda message: message)
def message_handler(message):
    # Каждая ветка завершает хендлер
    if message.text == 'Функции':
        logging.info(f'Пользователь {message.from_user.username} нажал на Функции')

        funcs_keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        add_buttons_to_keyboard(
            funcs_keyboard,
            [
                'Удалить диалог',
                'Задать поведение',
                'Меню',
            ]
        )

        bot.send_message(message.chat.id, strings.AVAILIBLE_FUNCS_DEST, reply_markup=funcs_keyboard)

    elif message.text == 'Удалить диалог':
        logging.info(f'Пользователь {message.from_user.username} нажал на Удалить диалог')

        modified_count = database.deactivate_all_messages(message.from_user.id)

        answer = strings.CONTEXT_DELETED if modified_count else strings.CONTEXT_ALREADY_DELETED

        bot.send_message(message.chat.id, answer)

    elif message.text == 'Задать поведение':
        logging.info(f'Пользователь {message.from_user.username} нажал на Задать поведение')

        bot.send_message(message.chat.id, strings.SET_SYSTEM_ROLE_FAQ)

    elif message.text == 'Меню':
        logging.info(f'Пользователь {message.from_user.username} нажал на Меню')

        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        add_buttons_to_keyboard(keyboard, ['Функции', 'О боте'])

        bot.send_message(message.chat.id, strings.START_MESSAGE, reply_markup=keyboard)

    elif message.text == 'О боте':
        logging.info(f'Пользователь {message.from_user.username} нажал О боте')

        msg = strings.ABOUT

        bot.send_message(message.chat.id, msg)

    else:
        logging.info(f'Пользователь {message.from_user.username} задал вопрос:\n{message.text}')
        answer = chatGPT.ask_gpt(message)

        if answer != strings.EXTERNAL_ERROR:
            markup = create_updated_markup('🔴 Удалить', callback_data='delete')
        else:
            markup = None

        bot.send_message(message.chat.id, answer, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'delete')
def delete_message_handler(call):
    logging.info(f'Пользователь {call.message.from_user.username} удалил ответ')

    database.deactivate_message(call.message.message_id - 1)

    markup = create_updated_markup('✅ Восстановить', callback_data='revive')

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='Удалено',
        reply_markup=markup,
    )


@bot.callback_query_handler(func=lambda call: call.data == 'revive')
def revive_message_handler(call):
    logging.info(f'Пользователь {call.message.from_user.username} восстановил ответ (не используется)')

    bot.send_message(call.message.chat.id, 'Восстановление пока недоступно')


bot.infinity_polling()
