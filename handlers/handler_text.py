import re
from utils.vk_helpers import send_message, get_vk_user, start_search, registration, check_token, show_random_from_search
from context import cancel_kb, refresh_token_kb
from handlers.handler_decorators import handlers, message_handler
from context import main_kb, registration_kb, show_list_kb
from database.db import show_favorites, show_blacklist, delete_favorite_people, delete_blacklist_people, get_user

def handler_message(user_id: int, message: str, state: str|None, **kwargs: 'Any') -> str | None:
    if state is None:
        if get_user(user_id):
            send_message(user_id, "С возвращением!", main_kb)
            return 'working'
        else:
            send_message(user_id, "Для начала работы необходимо пройти регистрацию", registration_kb)
            return 'registration'
    elif state == 'registration':
        return registration(user_id, message)
    else:
        if message in handlers:
            return handlers[message](user_id=user_id, message=message, state=state)
        else:
            return default_handler(user_id=user_id, message=message, state=state)

@message_handler("Зарегистрироваться")
def handle_registration(user_id: int, message: str, **kwargs: 'Any'):
    return registration(user_id, message)

@message_handler("Новый поиск")
def handle_search(user_id: int, **kwargs: 'Any'):
    if check_token(user_id):
        return start_search(user_id)
    else:
        send_message(user_id, 'Время жизни Вашего токена истекло - необходимо обновить', refresh_token_kb)
        return 'working'

@message_handler("Начать сессию")
def handle_start(user_id: int, **kwargs: 'Any'):
    show_random_from_search(user_id)
    return 'working'

@message_handler("Показать избранное")
def handle_show_favorite(user_id: int, **kwargs: 'Any'):
    favorites = show_favorites(user_id)
    vk_user = get_vk_user(user_id)
    humans = vk_user.users.get(user_ids=favorites, fields=['bdate', 'city', 'domain', 'has_photo', 'interests', 'sex'])
    if humans:
        send_message(user_id, '\n'.join([f"ID: {human['id']}  [https://vk.com/id{human['id']}|{human['first_name']} {human['last_name']}]" for human in humans]), show_list_kb)
        return 'show_favorites'
    else:
        send_message(user_id, "Твой список избранного пуст", main_kb)
        return 'working'


@message_handler("Показать 'черный' список")
def handle_show_blacklist(user_id: int, **kwargs: 'Any'):
    blacklist = show_blacklist(user_id)
    vk_user = get_vk_user(user_id)
    humans = vk_user.users.get(user_ids=blacklist, fields=['bdate', 'city', 'domain', 'has_photo', 'interests', 'sex'])
    if humans:
        send_message(user_id, '\n'.join([f"ID: {human['id']}  [https://vk.com/id{human['id']}|{human['first_name']} {human['last_name']}]" for human in humans]), show_list_kb)
        return 'show_blacklist'
    else:
        send_message(user_id, "Твой 'черный' список пуст", main_kb)
        return 'working'

@message_handler("Удалить пользователя")
def handle_remove_from_list(user_id: int, state: str|None, **kwargs: 'Any'):
    if state == 'show_favorites':
        send_message(user_id, "Скопируй и пришли мне ID одного или нескольких пользователей, и я удалю их из избранного", cancel_kb)
        return 'removing_favorite'
    elif state == 'show_blacklist':
        send_message(user_id, "Скопируй и пришли мне ID одного или нескольких пользователей, и я удалю их из 'черного' списка", cancel_kb)
        return 'removing_blacklist'

@message_handler("Отменить")
def handle_cancel(user_id: int, state: str|None, **kwargs: 'Any'):
    if state == 'removing_favorite' or state ==  'removing_blacklist':
        send_message(user_id, "Удаление отменено - выбери действие", main_kb)
        return 'working'

@message_handler("Вернуться")
def handle_cancel(user_id: int, **kwargs: 'Any'):
    send_message(user_id, "Выбери действие", main_kb)
    return 'working'

@message_handler("Очистить")
def handle_clear(user_id: int, state: str|None, **kwargs: 'Any'):
    if state == 'show_favorites':
        ids = show_favorites(user_id)
        delete_favorite_people(user_id, ids)
        send_message(user_id, "Список очищен - выбери действие", main_kb)
        return 'working'
    elif state ==  'show_blacklist':
        ids = show_blacklist(user_id)
        delete_blacklist_people(user_id, ids)
        send_message(user_id, "Список очищен - выбери действие", main_kb)
        return 'working'

@message_handler("Обновить токен")
def handle_refresh_token(user_id: int, message: str, **kwargs: 'Any'):
    return registration(user_id, message)

def default_handler(user_id: int, message: str, state: str|None, **kwargs: 'Any'):
    if state == 'removing_favorite':
        ids = list(map(int, re.findall(r'\d+', message)))
        if ids:
            try:
                delete_favorite_people(user_id, ids)
                send_message(user_id, 'Удаление прошло успешно. Вот твой обновленный список избранного')
                handle_show_favorite(user_id)
                return 'show_favorites'
            except:
                send_message(user_id, 'Произошла ошибка')
                return 'removing_favorite'
        else:
            send_message(user_id, 'В твоем сообщении не найдены ID', show_list_kb)
    elif state == 'removing_blacklist':
        ids = list(map(int, re.findall(r'\d+', message)))
        if ids:
            try:
                delete_blacklist_people(user_id, ids)
                send_message(user_id, "Удаление прошло успешно. Вот твой обновленный 'черный' список")
                handle_show_blacklist(user_id)
                return 'show_blacklist'
            except:
                send_message(user_id, 'Произошла ошибка')
                return 'removing_blacklist'
    else:
        send_message(user_id, 'Неопознанная команда - возврат в основное меню', main_kb)
        return 'working'