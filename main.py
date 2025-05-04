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
CLIENT_ID = os.getenv("CLIENT_ID")
DSN = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
os.environ["DSN"] = DSN
os.environ["GROUP_ID"] = GROUP_ID
os.environ["CLIENT_ID"] = CLIENT_ID
os.environ["APP_TOKEN"] = APP_TOKEN

from sqlalchemy import create_engine
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import sys, threading
from database.preparing_bd import initialize_db, create_db, create_tables
from handlers.handler_text import handler_message
from context import VK_SESSION
from handlers.handler_decorators import callback_routes
from datetime import datetime, timedelta
import handlers.handler_callback # необходим для инициализации модуля

# Словарь активных пользователей(кеш) {user_id:{'state': str, 'remove_at': datetime}
active_users = {}

# Создание Long poll с токеном бота
longpoll = VkBotLongPoll(VK_SESSION, group_id=GROUP_ID)

# Функция удаляющая неактивных пользователей из кеша раз в час
def clean_inactive_users(actives):
    now = datetime.now()
    for id_ in list(actives):
        if actives[id_]['remove_at'] <= now:
            del actives[id_]
            print(f"Удален пользователь {id_}")
    # Запланировать следующий запуск через 1 час
    threading.Timer(3600, clean_inactive_users, args=(actives,)).start()

# Тело самого бота
if __name__ == '__main__':
    # Подготовка базы
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
    print('Программа запущена')
    # Запуск таймера удаления неактивных пользователей
    clean_inactive_users(active_users)
    # Главный цикл, где бот прослушивает события
    for event in longpoll.listen():
        # Проверка на то, что пришло новое сообщение
        if event.type == VkBotEventType.MESSAGE_NEW:
            print(f'Событие нового сообщения от пользователя {event.obj['message']['from_id']}')
            user_id = event.obj['message']['from_id']
            text = event.obj['message']['text']
            date = event.obj['message']['date']
            if user_id not in active_users:
                active_users.update({user_id:{'state': None, 'remove_at': datetime.now()+timedelta(minutes=30)}})
            active_users[user_id]['state'] = handler_message(user_id=user_id, message=text, state=active_users.get(user_id).get('state'))
        # Проверка на событие с callback от inline-кнопок
        elif event.type == VkBotEventType.MESSAGE_EVENT:
            print(f"Событие от пользователя {event.obj['user_id']}")
            user_id = event.obj['user_id']
            payload = event.obj.get('payload', {})
            button = payload.get('button')
            if user_id not in active_users:
                active_users.update({user_id:{'state': None, 'remove_at': datetime.now()+timedelta(minutes=30)}})
            callback_handler = callback_routes.get(button)
            callback_handler(event)

