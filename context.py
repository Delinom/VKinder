import os, vk_api
from models.keyboard import KeyboardBuilder

VK_SESSION = vk_api.VkApi(token=os.getenv("APP_TOKEN"))
VK = VK_SESSION.get_api()

reaction_keyboard = KeyboardBuilder(inline=True)
reaction_keyboard.add_button("Нравится", {"button": "like", "id": None}, color="positive")
reaction_keyboard.add_button("Пропустить", {"button": "skip", "id": None}, color="primary")
reaction_keyboard.add_button("В ЧС", {"button": "black_list", "id": None}, color="negative")


