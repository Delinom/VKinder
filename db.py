import sqlalchemy
from flask import session
from sqlalchemy import create_engine, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, create_session
from models import User, SearchResult, Favourite, Blacklist
import os, secrets, requests, re, base64, hashlib

DSN = os.getenv('DSN')
print(DSN)
engine = create_engine(DSN)

def get_session():
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

def get_token():
    # 1. Сгенерировать code_verifier и code_challenge
    code_verifier = secrets.token_urlsafe(64)

    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")

    client_id = '53468644'
    redirect_uri = 'https://oauth.vk.com/blank.html'

    # 2. Сформировать URL для ручного перехода
    auth_url = (
        f"https://id.vk.com/authorize?"
        f"client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )

    print("Перейди по ссылке для авторизации:")
    print(auth_url)

    # 3. После авторизации VK перекинет на redirect_uri?code=XXXX
    # Вставь полученный `code` вручную:
    code_string = input("Скопируйте сюда адресную строку ответа")
    code = re.search(r'code=([^&]+)', code_string).group(1)
    device_id = re.search(r'device_id=([^&]+)', code_string).group(1)

    # 4. Обменять code на access_token
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

# функция, записывающая id пользователей в базу данных
def save_user(engine, user_id: int, first_name: str, last_name: str, sex: int, token: str):
    try:
        session = get_session()
        session.add(User(id_vk=user_id, first_name=first_name, last_name=last_name, sex=sex, token=token))
        session.commit()
        return True
    except IntegrityError:
        session.rollback()
        print("Пользователь уже присутствует в базе")
        return False

# Получение инфы о пользователе из базы
def get_user(user_id: int) -> User | None:
    session = get_session()
    print(user_id)
    return session.query(User).filter(User.id_vk == user_id).first()

# функция, записывающая id найденных людей
# def save_search_result(user_id: int, found_people: list[int]):
#     session = get_session()
#     chunks = [found_people[i:i + 10] for i in range(0, len(found_people), 10)]
#     for chunk in chunks:
#         result = SearchResult(id_user=user_id, id_found_people=chunk)
#         session.add(result)
#     session.commit()

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


# функция, добавляющая id людей в избранные пользователя
def save_favorite():
    pass

# функция, записывающая id людей в черный список пользователя
def save_blacklist():
    pass