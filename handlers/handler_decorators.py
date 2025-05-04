# Декоратор для обработки кнопок с callback
callback_routes = {}

def on_callback(button_name):
    def decorator(func):
        callback_routes[button_name] = func
        return func
    return decorator

# Декоратор для регистрации обработчиков по ключевому слову
handlers = {}

def message_handler(message_text):
    def decorator(func):
        handlers[message_text] = func
        return func
    return decorator