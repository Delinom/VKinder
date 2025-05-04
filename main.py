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
GROUP_ID = os.getenv("GROUP_ID")
DSN = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
os.environ["DSN"] = DSN
os.environ["APP_TOKEN"] = APP_TOKEN

import vk_api
from sqlalchemy import create_engine
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import sys
from database.preparing_bd import initialize_db, create_db, create_tables
from handlers.handler import handler
from context import VK, VK_SESSION
from utils.vk_helpers import callback_routes

# Словарь активных пользователей(кеш) {user_id:{'token': value, expire_time: value}
active_users = {}

# Создание Long poll с токеном бота
longpoll = VkBotLongPoll(VK_SESSION, group_id=GROUP_ID)

# Функция удаляющая неактивных пользователей раз в час
# def clean_active_users():
#     now = datetime.now()
#     for user_id in list(active_users):
#         if active_users[user_id] <= now:
#             del active_users[user_id]
#             print(f"Удален пользователь {user_id}")
#     # Запланировать следующий запуск через 1 час
#     threading.Timer(3600, clean_active_users).start()

# Тело самого бота
if __name__ == '__main__':
    # clean_active_users()
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

# Временная клавиатура
keyboard = VkKeyboard(one_time=False)
keyboard.add_button('Основная кнопка', color=VkKeyboardColor.POSITIVE)
keyboard.add_button('Еще кнопка', color=VkKeyboardColor.PRIMARY)

if __name__ == '__main__':
    print('Программа запущена')
    response = VK.groups.getById()
    response = vk_api.VkApi(token=APP_TOKEN).method('users.get')
    # Главный цикл, где бот прослушивает события
    for event in longpoll.listen():
        # Проверка на то, что пришло новое сообщение
        if event.type == VkBotEventType.MESSAGE_NEW:
            print(f'Событие нового сообщения от пользователя {event.obj['message']['from_id']}')
            user_id = event.obj['message']['from_id']
            text = event.obj['message']['text']
            date = event.obj['message']['date']
            active_users.update({user_id: handler(user_id, text, active_users.get(user_id), date)})
        # Проверка на событие с callback от inline-кнопок
        elif event.type == VkBotEventType.MESSAGE_EVENT:
            print(f"Событие от пользователя {event.obj['user_id']}")
            payload = event.obj.get('payload', {})
            button = payload.get('button')
            callback_handler = callback_routes.get(button)
            if callback_handler:
                callback_handler(event)
            else:
                print(f"Нет обработчика для кнопки: {button}")

