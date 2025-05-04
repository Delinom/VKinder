from datetime import datetime
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from database.orm_models import User, SearchResult, Favourite, Blacklist
import os

DSN = os.getenv('DSN')
print(DSN)
engine = create_engine(DSN)
Session = sessionmaker(bind=engine)

def get_session():
    try:
        session = Session()
        return session
    except SQLAlchemyError as e:
        print(f'Произошла ошибка при создании сессии: {e}')
        return None

# декоратор-обработчик ошибок
def handle_db_errors(func_):
    def wrapper(*args, **kwargs):
        session = get_session()
        if session is None:
            return None
        try:
            result = func_(session, *args, **kwargs)
            session.commit()
            return result
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Произошла ошибка при работе с базой данных: {e}")
            return False
        finally:
            session.close()
    return wrapper


# функция, записывающая id пользователей в базу данных
@handle_db_errors
def save_user(session, user_id: int, first_name: str, last_name: str, sex: int, token: str, token_expire: datetime):
    user = session.query(User).get(user_id)
    if user:
        user.first_name=first_name
        user.last_name=last_name
        user.sex=sex
        user.token=token
        user.token_expire=token_expire
    else:
        session.add(User(id_vk=user_id, first_name=first_name, last_name=last_name, sex=sex, token=token, token_expire=token_expire))
    return True

# Получение информации о пользователе из базы
@handle_db_errors
def get_user(session, user_id: int) -> User | None:
    user = session.query(User).filter(User.id_vk == user_id).first()
    if user:
        session.expunge(user)
    return user

# сохранение результатов поиска в бд
@handle_db_errors
def save_search_result(session, user_id: int, found_people: set[int]):
    results = [SearchResult(id_user=user_id, id_found_people=user) for user in found_people]
    session.add_all(results)
    return True

# получение случайного человека из результатов поиска
@handle_db_errors
def get_user_from_search(session, user_id: int) -> int | None:
    result = session.query(SearchResult.id_found_people).filter(SearchResult.id_user == user_id).order_by(func.random()).limit(1).scalar()
    return result

# функция, добавляющая id людей в избранные пользователя
@handle_db_errors
def save_favorite(session, user_id: int, favorites_people_id: int):
    result = Favourite(id_user=user_id, id_favorites_people=favorites_people_id)
    session.add(result)
    return True

# функция, выдающая список понравившихся людей
@handle_db_errors
def show_favorites(session, user_id: int) -> list[int] | None:
    favorites = session.query(Favourite.id_favorites_people).filter(Favourite.id_user == user_id).all()
    return [fav[0] for fav in favorites]

# функция, добавляющая id людей в черный список пользователя
@handle_db_errors
def save_blacklist(session, user_id: int, bad_people_id: int):
    result = Blacklist(id_user=user_id, id_blacklist_people=bad_people_id)
    session.add(result)
    return True

# функция, выдающая список людей из черного списка
@handle_db_errors
def show_blacklist(session, user_id: int) -> list[int] | None:
    blacklist = session.query(Blacklist.id_blacklist_people).filter(Blacklist.id_user == user_id).all()
    return [bad[0] for bad in blacklist]

# функция для удаления людей из избранных
@handle_db_errors
def delete_favorite_people(session, user_id: int, favorites_id: list[int]):
    session.query(Favourite).filter(Favourite.id_user == user_id, Favourite.id_favorites_people.in_(favorites_id)).delete(synchronize_session=False)
    return True

# функция для удаления людей из черного списка
@handle_db_errors
def delete_blacklist_people(session, user_id: int, bad_people_id: list[int]):
    session.query(Blacklist).filter(Blacklist.id_user == user_id, Blacklist.id_blacklist_people.in_(bad_people_id)).delete(synchronize_session=False)
    return True

# Функция для удаления записей о человеке из таблицы SearchResult после того,
# как пользователь отреагировал на его профиль (пропустил/добавил в избранное/в чс), чтобы избежать дублирования
@handle_db_errors
def delete_from_search(session, user_id: int, random_human_id: int):
    session.query(SearchResult).filter(SearchResult.id_user == user_id, SearchResult.id_found_people == random_human_id).delete(synchronize_session=False)
    return True

# Функция для удаления всех записей в таблице SearchResult при повторном запуске бота,
# чтобы избежать дублирования старых записей
@handle_db_errors
def delete_all_from_search(session, user_id: int):
    session.query(SearchResult).filter(SearchResult.id_user == user_id).delete(synchronize_session=False)
    return True