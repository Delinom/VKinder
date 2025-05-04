import os, vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from models.keyboard import KeyboardBuilder

# Модуль контекста: сессия и клавиатуры
VK_SESSION = vk_api.VkApi(token=os.getenv("APP_TOKEN"))
VK = VK_SESSION.get_api()

reaction_kb = KeyboardBuilder(inline=True)
reaction_kb.add_button("Нравится", {"button": "like", "id": None}, color="positive")
reaction_kb.add_button("Пропустить", {"button": "skip", "id": None}, color="primary")
reaction_kb.add_button("В ЧС", {"button": "black_list", "id": None}, color="negative")
reaction_kb.add_button("Завершить", {"button": "stop", "id": None}, color="primary")


main_kb = VkKeyboard(inline=False, one_time=False)
main_kb.add_button("Начать сессию", color=VkKeyboardColor.POSITIVE)
main_kb.add_line()
main_kb.add_button("Показать избранное", color=VkKeyboardColor.POSITIVE)
main_kb.add_button("Показать 'черный' список", color=VkKeyboardColor.NEGATIVE)
main_kb.add_line()
main_kb.add_button("Новый поиск", color=VkKeyboardColor.POSITIVE)
main_kb = main_kb.get_keyboard()

registration_kb = VkKeyboard(inline=False, one_time=True)
registration_kb.add_button("Зарегистрироваться", color=VkKeyboardColor.POSITIVE)
registration_kb = registration_kb.get_keyboard()

refresh_token_kb = VkKeyboard(inline=False, one_time=True)
refresh_token_kb.add_button("Обновить токен", color=VkKeyboardColor.POSITIVE)
refresh_token_kb = refresh_token_kb.get_keyboard()

start_search_kb = VkKeyboard(inline=False, one_time=True)
start_search_kb.add_button("Новый поиск", color=VkKeyboardColor.POSITIVE)
start_search_kb = start_search_kb.get_keyboard()

show_list_kb = VkKeyboard(inline=False, one_time=True)
show_list_kb.add_button("Вернуться", color=VkKeyboardColor.POSITIVE)
show_list_kb.add_line()
show_list_kb.add_button("Удалить пользователя", color=VkKeyboardColor.NEGATIVE)
show_list_kb.add_button("Очистить", color=VkKeyboardColor.NEGATIVE)
show_list_kb = show_list_kb.get_keyboard()

cancel_kb = VkKeyboard(inline=False, one_time=True)
cancel_kb.add_button("Отменить", color=VkKeyboardColor.POSITIVE)
cancel_kb = cancel_kb.get_keyboard()



