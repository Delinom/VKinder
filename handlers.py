from classes import User
from datetime import datetime
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor, VkKeyboardButton
from random import randint

handlers = {}

# Сюда нужно будет ввести токен пользователя, которому будет происходить поиск
my_token = ''

# Формирование клавиатуры для показа человека. Тоже временно
keyboard_main = VkKeyboard(one_time=True)
keyboard_main.add_button("Нравится", color=VkKeyboardColor.POSITIVE)
keyboard_main.add_button("Пропустить", color=VkKeyboardColor.SECONDARY)
keyboard_main.add_line()
keyboard_main.add_button("В ЧС!!!", color=VkKeyboardColor.NEGATIVE)

# Декораток обработчков сообщений
def on_keyword(keyword):
    def decorator(func):
        handlers[keyword] = func
        return func
    return decorator

# Обработчик сообщения боту на старт поиска по данным его профиля
@on_keyword("Найди мне пару")
def handle_hello(event, vk):
    # Сбор его данных
    user_info = vk.users.get(user_ids=event.user_id, fields=['bdate', 'city', 'domain', 'has_photo', 'interests', 'sex'])[0]
    # Очередной временный принт
    print(user_info)

    # Вместо этого нужно будет обновить данные этого пользователя в базе
    user = User(event.user_id)
    mapping = {
        'name': user_info.get('first_name'),
        'last_name': user_info.get('last_name'),
        'sex': user_info.get('sex'),
        'city_id': user_info.get('city', {}).get('id'),
        'bdate': user_info.get('bdate')
    }
    for key, values in mapping.items():
        setattr(user, key, values)

    # Подготовка к поиску
    birth_date = datetime.strptime(user.bdate, "%d.%m.%Y")
    user.age = (datetime.now() - birth_date).days // 365
    opposite_sex = 1 if user.sex == 2 else 2 # 1 и 2 это мужчина или женщина. Или наоборот - не помню, да и не суть
    # Допуск +/- 5 лет
    min_age = user.age - 5
    max_age = user.age + 5

    # Создание сессии уже от имени пользователя и запрос на поиск
    vk_session_user = vk_api.VkApi(token=my_token)
    vk_user = vk_session_user.get_api()
    response = vk_user.users.search(
        sex=opposite_sex,
        city=user.city_id,
        age_from=min_age,
        age_to=max_age,
        count=100
    )
    print(response)
    # Временный краткий вывод результатов, который нужно будет сохранить в таблицу SearchResult
    for human in response['items']:
        print(f"ID: {human['id']}, Имя: {human['first_name']} {human['last_name']}")
    # Рандомный человек для предложки
    human = vk_user.users.get(user_ids=response['items'][randint(0, 100)]['id'], fields=['bdate', 'city', 'domain', 'has_photo', 'interests', 'sex'])[0]
    # Формирование и отправка сообщения
    vk.messages.send(
        user_id=event.user_id,
        message=f"{human['first_name']} {human['last_name']}\nПол: {'ж' if human['sex'] == 1 else 'м'}\nГород: {human['city']['title']}",
        keyboard=keyboard_main.get_keyboard(),
        random_id=vk_api.utils.get_random_id()
    )
