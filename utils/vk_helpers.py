import vk_api
from context import VK
from database.db import get_user


# Декоратор для обработки кнопок с callback
callback_routes = {}
def on_callback(button_name):
    def decorator(func):
        callback_routes[button_name] = func
        return func
    return decorator

# Функция отправки сообщения
def send_message(user_id: int, message: str, keyboard=None, attachment=None):
    VK.messages.send(
        user_id=user_id,
        message=message,
        attachment=attachment,
        keyboard=keyboard,
        random_id=vk_api.utils.get_random_id()
    )

# Функция удаления сообщения
def delete_message(peer_id: int, cmids: int):
    VK.messages.delete(
        peer_id=peer_id,  # ID беседы
        cmids=cmids,  # cmid — conversation_message_id
        delete_for_all=1,  # Удалить для всех
        group_id=230213428  # ID сообщества
    )

# Функция получения api с токеном пользователя
def get_vk_user(user_id):
    token = get_user(user_id).token
    vk_session = vk_api.VkApi(token=token)
    vk_user = vk_session.get_api()
    return vk_user

