from database.db import delete_from_search, save_favorite, save_blacklist
from utils.vk_helpers import send_message, delete_message, show_random_from_search
from context import main_kb
from handlers.handler_decorators import on_callback

# Обработчики кнопок inline-клавиатуры
@on_callback('like')
def handle_like(event):
    user_id = event.obj.get('user_id')
    human_id = event.obj.get('payload').get('id')
    save_favorite(user_id, human_id)
    delete_message(peer_id=user_id, cmids=event.obj['conversation_message_id'])
    delete_from_search(user_id, human_id)
    show_random_from_search(user_id)

@on_callback('skip')
def handle_skip(event):
    user_id = event.obj.get('user_id')
    delete_message(peer_id=user_id, cmids=event.obj['conversation_message_id'])
    show_random_from_search(user_id)

@on_callback('black_list')
def handle_black_list(event):
    user_id = event.obj.get('user_id')
    human_id = event.obj.get('payload').get('id')
    save_blacklist(user_id, human_id)
    delete_message(peer_id=user_id, cmids=event.obj['conversation_message_id'])
    delete_from_search(user_id, human_id)
    show_random_from_search(user_id)

@on_callback('stop')
def handle_stop(event):
    user_id = event.obj.get('user_id')
    delete_message(peer_id=user_id, cmids=event.obj['conversation_message_id'])
    send_message(user_id, "Сессия завершена", main_kb)



