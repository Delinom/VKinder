import os
from dotenv import load_dotenv
# Получение переменных окружения
load_dotenv()
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
APP_TOKEN = os.getenv("APP_TOKEN")
DSN = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
os.environ["DSN"] = DSN

import vk_api
from sqlalchemy import create_engine
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from handlers import handlers
import sys, threading
from preparing_bd import initialize_db, create_db, create_tables
from db import save_user, get_token
from datetime import datetime, timedelta

# # Получение переменных окружения
# load_dotenv()
# DB_NAME = os.getenv("DB_NAME")
# DB_USER = os.getenv("DB_USER")
# DB_PASSWORD = os.getenv("DB_PASSWORD")
# DB_HOST = os.getenv("DB_HOST")
# DB_PORT = os.getenv("DB_PORT")
# APP_TOKEN = os.getenv("APP_TOKEN")
# DSN = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# Словарь активных пользователей(кеш) {user_id:{'token': value, expire_time: value}
active_users = {}

#Создаем бота ВК через vk_api с токеном приложения
vk_session = vk_api.VkApi(token=APP_TOKEN)
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

#Инициализация клавиатуры. Скорее всего, временная, для примера. Потом переместится в отдельный модуль
keyboard = VkKeyboard(one_time=True)
keyboard.add_button("Найди мне пару", color=VkKeyboardColor.POSITIVE)
# keyboard.add_button("Помощь", color=VkKeyboardColor.PRIMARY)
# keyboard.add_line()  # Переход на новую строку
# keyboard.add_button("Выход", color=VkKeyboardColor.NEGATIVE)

# Функция удаляющая неактивных пользователей раз в час
def clean_active_users():
    now = datetime.now()
    for user_id in list(active_users):
        if active_users[user_id] <= now:
            del active_users[user_id]
            print(f"Удален пользователь {user_id}")
    # Запланировать следующий запуск через 1 час
    threading.Timer(3600, clean_active_users).start()

# Тело самого бота
if __name__ == '__main__':
    clean_active_users()
    engine = create_engine(DSN)
    if initialize_db(DSN):
        print(f"База данных '{DB_NAME}' уже существует")
    else:
        if create_db(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT):
            print('База успешно создана')
        else:
            print(f"Произошла ошибка при создании базы. Попробуйте создать базу вручную")
            input('Нажмите любую клавишу для завершения программы')
            sys.exit()
    create_tables(engine)

    # Главный цикл, где бот прослушивает события
    for event in longpoll.listen():
        # Проверка на то, что пришло новое сообщение и оно адресовано боту
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            # Отладочный принт
            print(f"Сообщение от {event.user_id}: {event.text}")
            # Проверка наличия пользователя в кеше и в БД
            if user_id not in active_users:
                user_info = vk.users.get(user_ids=event.user_id, fields=['sex'])[0]
                active_users[user_id] = datetime.now() + timedelta(hours=1)
                while True:
                    try:
                        token, refresh_token = get_token()
                        print(len(token), token)
                        break
                    except Exception:
                        print('Произошла ошибка - попробуй еще раз')
                if save_user(engine, event.user_id, user_info['first_name'], user_info['last_name'], user_info['sex'], token):
                    # Регистрация в базе и приветственное сообщение
                    vk.messages.send(
                        user_id=event.user_id,
                        message="Добро пожаловать! Для начала работы вам необходимо получить токен",
                        keyboard=keyboard.get_keyboard(),
                        random_id=vk_api.utils.get_random_id()
                    )
                    continue
            # Если пользователь уже в базе, то передача текста сообщения в обработчик
            text = event.text
            for keyword, handler in handlers.items():
                if keyword in text:
                    handler(event, vk)
                    break

