import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from handlers import handlers
from classes import User
import configparser

# Парсим глобальные переменные из settings.ini, а точнее, токен приложения
config = configparser.ConfigParser()
config.read('settings.ini')
APP_TOKEN = config['Tokens']['app_token']
#Создаем бота ВК через vk_api с токеном приложения
vk_session = vk_api.VkApi(token=APP_TOKEN)
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

#Инициализация клавиатары. Скорее всего, временная, для примера. Потом переместится в отдельный модуль
keyboard = VkKeyboard(one_time=True)
keyboard.add_button("Найди мне пару", color=VkKeyboardColor.POSITIVE)
# keyboard.add_button("Помощь", color=VkKeyboardColor.PRIMARY)
# keyboard.add_line()  # Переход на новую строку
# keyboard.add_button("Выход", color=VkKeyboardColor.NEGATIVE)


# Заглушка вместо результата запроса на наличие пользователя в бд
user_in_db = 1


# Тело самого бота
if __name__ == '__main__':
    # Главный цикл, где бот прослушивает события
    for event in longpoll.listen():
        # Проверка на то, что пришло новое сообщение и оно адресовано боту
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            # Отладочный принт
            print(f"Сообщение от {event.user_id}: {event.text}")
            # Тут должен быть запрос в базу на наличие в нем пользователя и если его там нет, то регистрация его в базе
            if event.user_id != user_in_db:
                # Регистрация в базе и приветственное сообщение
                user_in_db = event.user_id
                vk.messages.send(
                    user_id=event.user_id,
                    message="Добро пожаловать! Сейчас тебя зарегистрирую и начнем!",
                    keyboard=keyboard.get_keyboard(),
                    random_id=vk_api.utils.get_random_id()
                )
                continue
            # Если пользователь уже в базе, то передача текста сообщения в обработчик
            else:
                text = event.text
                for keyword, handler in handlers.items():
                    if keyword in text:
                        handler(event, vk)
                        break

