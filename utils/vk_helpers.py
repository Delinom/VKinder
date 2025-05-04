import base64, hashlib, re, secrets, os
from datetime import datetime, timedelta
import requests
import vk_api
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from context import VK, main_kb, reaction_kb
from database.db import get_user, delete_all_from_search, save_user, show_favorites, show_blacklist, get_user_from_search, save_search_result
from database.orm_models import User

DSN = os.getenv('DSN')
GROUP_ID = os.getenv('GROUP_ID')
CLIENT_ID = os.getenv('CLIENT_ID')
engine = create_engine(DSN)
code_verifiers = {}

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
        peer_id=peer_id,
        cmids=cmids,  # conversation_message_id
        delete_for_all=1,
        group_id=GROUP_ID
    )

# Функция получения api с токеном пользователя
def get_vk_user(user_id):
    token = get_user(user_id).token
    vk_session = vk_api.VkApi(token=token)
    vk_user = vk_session.get_api()
    return vk_user

def start_search(user_id: int):
    delete_all_from_search(user_id)
    user = get_user(user_id)
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
        count=15
    )
    # Сохранение результатов
    exclude_set = set(show_favorites(user_id) + show_blacklist(user_id))
    search_result = set(human['id'] for human in response['items'] if human['is_closed']==False)
    if exclude_set:
        search_result.difference_update(exclude_set)
    if search_result:
        save_search_result(user_id=user_id, found_people=search_result)
        show_random_from_search(user_id)
        return 'working'
    else:
        send_message(user_id, 'Для твоего профиля больше нет совпадений. Для нового поиска измени данные')
        return 'working'

def registration(user_id: int, message: str):
    if message.startswith('https://oauth.vk.com/blank.html?code='):
        try:
            token, token_expire = get_token(user_id, message)
            token_expire = datetime.now()+timedelta(seconds=token_expire)
            user_info = get_user_info(user_id, token)
            if user_info:
                if len(user_info) == 5:
                    save_user(user_id=user_id, first_name=user_info['first_name'], last_name=user_info['last_name'], sex=user_info['sex'], token=token, token_expire=token_expire)
                    send_message(user_id, "Пользователь в базе - можем начинать", main_kb)
                    return 'working'
                else:
                    translates = {'first_name': 'Имя',
                                  'last_name': 'Фамилия',
                                  'city': 'Город',
                                  'sex': 'Пол',
                                  'bdate': 'Дата рождения'}
                    missing_fields = [translates[field] for field in translates if user_info.get(field) is None]
                    send_message(user_id, f"В вашем профиле отсутствуют, либо некорректно заполнены поля {', '.join(missing_fields)}\nДля продолжения работы заполните их и повторите регистрацию")
                    return None
            else:
                send_message(user_id, "К сожалению Ваш токен не прошел валидацию. Повторите регистрацию")
                return None
        except:
            send_message(user_id, "Произошла ошибка - повторите регистрацию заново")
            return None
    else:
        text = generate_code_url(user_id)
        send_message(user_id, f"Перейди по ссылке, разреши доступ и отправь мне адресную строку, которая пришла в ответ\n{text}")
        return 'registration'

# Функция получения токена
def get_token(user_id: int, code_string: str) -> tuple[str]|bool:
    code_verifier = code_verifiers.pop(user_id)
    redirect_uri = 'https://oauth.vk.com/blank.html'
    code = re.search(r'code=([^&]+)', code_string).group(1)
    device_id = re.search(r'device_id=([^&]+)', code_string).group(1)

    # Обмен code на access_token
    token_url = "https://id.vk.com/oauth2/auth"

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': CLIENT_ID,
        'device_id': device_id,
        'redirect_uri': redirect_uri,
        'code_verifier': code_verifier,
    }

    response = requests.post(token_url, data=data)

    if response.ok:
        response = response.json()
        token = response['access_token']
        expires_in = response['expires_in']
        print("Токен получен:")
        return token, expires_in
    else:
        print("Ошибка:")
        print(response.status_code, response.text)
        return False

def generate_code_url(user_id: int) -> str:

    # Генерация code_verifier и code_challenge
    code_verifier = secrets.token_urlsafe(64)
    code_verifiers.update({user_id: code_verifier})

    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")
    redirect_uri = 'https://oauth.vk.com/blank.html'

    # Формирование URL
    auth_url = (
        f"https://id.vk.com/authorize?"
        f"client_id={CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )

    return auth_url

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

# Проверка на наличие ошибок в ответе на запрос
def check_response(response):
    if 'error' in response:
        print(response['error']['error_msg'])
        return False
    else:
        return True

# Сервисная функция создания сессии
def get_session() -> Session:
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

# Проверка токена на валидность
def check_token(user_id: int) -> bool:
    user = get_user(user_id)
    params = {'access_token': user.token, 'v': '5.199'}
    response = requests.get('https://api.vk.com/method/users.get', params=params).json()
    if check_response(response):
        print(f'Ключ пользователя {user_id} ключ валиден')
        return True
    else:
        return False

def user_in_db(user_id: int) -> User|None:
    session = get_session()
    return session.query(User).filter_by(id_vk=user_id).first()

def show_random_from_search(user_id: int):
    # Рандомный человек для предложки
    vk_user = get_vk_user(user_id)
    human_id = get_user_from_search(user_id)
    if human_id is None:
        send_message(user_id, "Твой поиск опустел - запусти новый", main_kb)
    else:
        human = vk_user.users.get(user_ids=human_id, fields=['bdate', 'city', 'domain', 'has_photo', 'interests', 'sex'])[0]
        # Формирование и отправка сообщения
        send_message(user_id=user_id,
                     message = f"[https://vk.com/id{human_id}|{human['first_name']} {human['last_name']}]",
                     keyboard=reaction_kb.get_keyboard(human_id),
                     attachment=get_top_photos(vk_user.photos.get(owner_id=human_id, album_id='profile', extended=True))
                     )

def get_top_photos(response: dict, count: int = 3) -> str:
    sorted_photos = sorted(response['items'], key=lambda x: x.get('likes', {}).get('count', 0), reverse=True)
    top_photos = sorted_photos[:count]
    # Формирование attachment строк
    attachments = [f"photo{item['owner_id']}_{item['id']}" for item in top_photos]
    return ",".join(attachments)
