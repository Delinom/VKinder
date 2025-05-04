import os, secrets, requests, re, base64, hashlib, vk_api
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from datetime import datetime
from database.orm_models import User, SearchResult
from database.db import delete_all_from_search, delete_from_search, save_favorite, save_blacklist
from utils.vk_helpers import send_message, delete_message, get_vk_user
from context import VK, reaction_keyboard
from utils.vk_helpers import on_callback

DSN = os.getenv('DSN')
engine = create_engine(DSN)
keyboard = VkKeyboard(one_time=True)
keyboard.add_button("Зарегистрироваться", color=VkKeyboardColor.POSITIVE)
code_verifiers = {}

def save_search_result(user_id: int, found_people: list[int]):
    session = get_session()
    for user in found_people:
        result = SearchResult(id_user=user_id, id_found_people=user)
        session.add(result)
    session.commit()

def get_user_from_search(user_id: int) -> int:
    session = get_session()
    result = (session.query(SearchResult.id_found_people).filter(SearchResult.id_user == user_id).order_by(func.random()).limit(1).scalar())
    return result

# Сервисная функция создания сессии
def get_session() -> Session:
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

# Проверка токена на валидность
def check_token(user_id: int) -> bool:
    session = get_session()
    user = session.query(User).filter(User.id_vk == user_id).first()
    params = {'access_token': user.token, 'v': '5.199'}
    response = requests.get('https://api.vk.com/method/users.get', params=params).json()
    if check_response(response):
        print(
            f'Добро пожаловать, {response['response'][0]['first_name']} {response['response'][0]['last_name']}, Ваш ключ валиден')

# Проверка на наличие ошибок в ответе на запрос
def check_response(response):
    if 'error' in response:
        print(response['error']['error_msg'])
        input('Для завершения программы нажмите Enter')
        exit()
    else:
        return True

def get_user_info(user_id: int, token: str) -> dict|bool:
    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()
    user_info = vk.users.get(user_ids=user_id, fields="first_name,last_name,city,sex,bdate")
    if check_response(user_info):
        expected_fields = ["first_name", "last_name", "city", "sex", "bdate"]
        missing_fields = []
        for field in expected_fields:
            if field not in user_info[0]:
                missing_fields.append(field)
        if missing_fields:
            result = missing_fields
        else:
            result = {field: user_info[0].get(field) for field in ['first_name', 'last_name', 'sex']}
            city = user_info[0].get('city', {}).get('id')
            if city:
                result.update({'city': city})
            bdate = user_info[0].get('bdate')
            if bdate and bdate.count('.') == 2:
                result.update({'bdate': bdate})
        return result
    else:
        return False

# Функция получения токена
def generate_code_url(user_id: int) -> str:

    # Генерация code_verifier и code_challenge
    code_verifier = secrets.token_urlsafe(64)
    code_verifiers.update({user_id: code_verifier})

    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")

    client_id = '53468644'
    redirect_uri = 'https://oauth.vk.com/blank.html'

    # Формирование URL
    auth_url = (
        f"https://id.vk.com/authorize?"
        f"client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )

    return auth_url

def get_token(user_id: int, code_string: str) -> tuple[str]|bool:
    code_verifier = code_verifiers.pop(user_id)
    client_id = '53468644'
    redirect_uri = 'https://oauth.vk.com/blank.html'
    code = re.search(r'code=([^&]+)', code_string).group(1)
    device_id = re.search(r'device_id=([^&]+)', code_string).group(1)

    # Обмен code на access_token
    token_url = "https://id.vk.com/oauth2/auth"

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': client_id,
        'device_id': device_id,
        'redirect_uri': redirect_uri,
        'code_verifier': code_verifier,
    }

    response = requests.post(token_url, data=data)

    if response.ok:
        response = response.json()
        refresh_token = response['refresh_token']
        token = response['access_token']
        print("Токен получен:")
        return token, refresh_token
    else:
        print("Ошибка:")
        print(response.status_code, response.text)
        return False

def registration(user_id: int, message: str):
    if message.startswith('https://oauth.vk.com/blank.html?code='):
        try:
            token = get_token(user_id, message)[0]
            user_info = get_user_info(user_id, token)
            if user_info:
                if len(user_info) == 5:
                    save_user(user_id=user_id, first_name=user_info['first_name'], last_name=user_info['last_name'], sex=user_info['sex'], token=token)
                    keyboard = VkKeyboard(one_time=False)
                    keyboard.add_button("Запустить поиск", color=VkKeyboardColor.POSITIVE)
                    VK.messages.send(
                        user_id=user_id,
                        message="Пользователь в базе - можем начинать",
                        keyboard=keyboard.get_keyboard(),
                        random_id=vk_api.utils.get_random_id()
                    )
                    return None
                else:
                    translates = {'first_name': 'Имя',
                                  'last_name': 'Фамилия',
                                  'city': 'Город',
                                  'sex': 'Пол',
                                  'bdate': 'Дата рождения'}
                    missing_fields = [translates[field] for field in translates if user_info.get(field) is None]
                    VK.messages.send(
                        user_id=user_id,
                        message=f"В вашем профиле отсутствуют, либо некорректно заполнены поля {', '.join(missing_fields)}\nДля продолжения работы заполните их и повторите регистрацию",
                        random_id=vk_api.utils.get_random_id()
                    )
                    return None
            else:
                VK.messages.send(
                    user_id=user_id,
                    message=f"К сожалению Ваш токен не прошел валидацию. Повторите регистрацию",
                    random_id=vk_api.utils.get_random_id()
                )
                return None
        except:
            VK.messages.send(
                user_id=user_id,
                message=f"Произошла ошибка - повторите регистрацию заново",
                random_id=vk_api.utils.get_random_id()
            )
            return None
    else:
        text = generate_code_url(user_id)
        VK.messages.send(
            user_id=user_id,
            message=f"Перейди по ссылке, разреши доступ и отправь мне адресную строку, которая пришла в ответ\n{text}",
            random_id=vk_api.utils.get_random_id()
        )
        return 'registration'

# функция, записывающая id пользователей в базу данных
def save_user(user_id: int, first_name: str, last_name: str, sex: int, token: str):
    try:
        session = get_session()
        session.add(User(id_vk=user_id, first_name=first_name, last_name=last_name, sex=sex, token=token))
        session.commit()
        return True
    except IntegrityError:
        session.rollback()
        print("Пользователь уже присутствует в базе")
        return False

def user_in_db(user_id: int) -> User|None:
    session = get_session()
    return session.query(User).filter_by(id_vk=user_id).first()

def start_search(user_id: int):
    # delete_all_from_search(user_id)
    user = user_in_db(user_id)
    user_info = VK.users.get(user_ids=user_id, fields=['bdate', 'city', 'domain', 'has_photo', 'interests', 'sex'])[0]
    birth_date = datetime.strptime(user_info.get('bdate'), "%d.%m.%Y")
    city_id = user_info.get('city', {}).get('id')
    user.age = (datetime.now() - birth_date).days // 365
    opposite_sex = 1 if user.sex == 2 else 2
    # Допуск +/- 5 лет
    min_age = user.age - 5
    max_age = user.age + 5

    # Создание сессии уже от имени пользователя и запрос на поиск
    vk_user = get_vk_user(user_id)
    response = vk_user.users.search(
        sex=opposite_sex,
        city=city_id,
        age_from=min_age,
        age_to=max_age,
        count=100
    )
    # Сохранение результатов
    save_search_result(user_id=user_id, found_people=[human['id'] for human in response['items'] if human['is_closed']==False])
    show_random_from_search(user_id)

def show_random_from_search(user_id: int):
    # Рандомный человек для предложки
    vk_user = get_vk_user(user_id)
    human_id = get_user_from_search(user_id)
    human = vk_user.users.get(user_ids=human_id, fields=['bdate', 'city', 'domain', 'has_photo', 'interests', 'sex'])[0]
    # Формирование и отправка сообщения
    send_message(user_id=user_id,
                 message = f"[https://vk.com/id{human_id}|{human['first_name']} {human['last_name']}]",
                 keyboard=reaction_keyboard.get_keyboard(human_id),
                 attachment=get_top_photos(vk_user.photos.get(owner_id=human_id, album_id='profile', extended=True))
                 )

def get_top_photos(response: dict, count: int = 3) -> str:
    sorted_photos = sorted(response['items'], key=lambda x: x.get('likes', {}).get('count', 0), reverse=True)
    top_photos = sorted_photos[:count]
    # Формирование attachment строк
    attachments = [f"photo{item['owner_id']}_{item['id']}" for item in top_photos]
    return ",".join(attachments)

def handler(user_id: int, message: str, state: str, time: datetime) -> str|None:
    if state is None:
        if message == 'Зарегистрироваться':
            return registration(user_id, message)
        elif user_in_db(user_id):
            if message == 'Запустить поиск':
                return start_search(user_id)
            else:
                keyboard = VkKeyboard(one_time=False)
                keyboard.add_button("Запустить поиск", color=VkKeyboardColor.POSITIVE)
                send_message(user_id, "Пользователь в базе - можем начинать", keyboard.get_keyboard())
                return None
        else:
            keyboard = VkKeyboard(one_time=True)
            keyboard.add_button("Зарегистрироваться", color=VkKeyboardColor.POSITIVE)
            send_message(user_id, "Для начала работы необходимо пройти регистрацию", keyboard.get_keyboard())
            return None
    elif state == 'registration':
        return registration(user_id, message)

@on_callback('like')
def handle_like(event):
    user_id = event.obj.get('user_id')
    human_id = event.obj.get('payload').get('id')
    save_favorite(user_id, human_id)
    delete_message(peer_id=user_id, cmids=event.obj['conversation_message_id'])
    # delete_from_search(user_id, human_id)
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



