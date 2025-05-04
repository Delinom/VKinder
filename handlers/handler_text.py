@message_handler("привет")
def handle_hello(event):
    vk.messages.send(
        user_id=event.message.from_id,
        message="Привет! 👋",
        random_id=0
    )

@message_handler("помощь")
def handle_help(event):
    vk.messages.send(
        user_id=event.message.from_id,
        message="Вот список команд: привет, помощь",
        random_id=0
    )