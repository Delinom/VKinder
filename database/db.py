from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from database.orm_models import User, SearchResult, Favourite, Blacklist
import os, secrets, requests, re, base64, hashlib

DSN = os.getenv('DSN')
print(DSN)
engine = create_engine(DSN)

def get_session():
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        return session
    except SQLAlchemyError as e:
        print(f'Произошла ошибка при создании сессии: {e}')
        return None


# функция, записывающая id пользователей в базу данных
def save_user(engine, user_id: int, first_name: str, last_name: str, sex: int, token: str):
    session = get_session()
    if session is None:
        print('Не удалось создать сессию для работы с базой данных')
        return False
    else:
        try:
            session.add(User(id_vk=user_id, first_name=first_name, last_name=last_name, sex=sex, token=token))
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            print("Произошла ошибка при работе с базой данных: {e}")
            return False

# Получение инфы о пользователе из базы
def get_user(user_id: int) -> User | None:
    session = get_session()
    if session is None:
        print('Не удалось создать сессию для работы с базой данных')
        return None
    else:
        try:
            result = session.query(User).filter(User.id_vk == user_id).first()
            return result
        except SQLAlchemyError as e:
            session.rollback()
            print(f'Произошла ошибка при работе с базой данных: {e}')
            return None
        finally:
            session.close()

# сохранение результатов поиска в бд
def save_search_result(user_id: int, found_people: list[int]):
    session = get_session()
    if session is None:
        print('Не удалось создать сессию для работы с базой данных')
        return False
    else:
        try:
            for user in found_people:
                result = SearchResult(id_user=user_id, id_found_people=user)
                session.add(result)
            session.commit()
            return True
        except SQLAlchemyError as e:
            print(f'Произошла ошибка при работе с базой данных: {e}')
            return False
        finally:
            session.close()

# получение случайного человека из результатов поиска
def get_user_from_search(user_id: int) -> int:
    session = get_session()
    if session is None:
        print('Не удалось создать сессию для работы с базой данных')
        return False
    else:
        try:
            result = (session.query(SearchResult.id_found_people).filter(SearchResult.id_user == user_id).order_by(
                func.random()).limit(1).scalar())
            return result
        except SQLAlchemyError as e:
            print(f'Произошла ошибка при работе с базой данных: {e}')
            return False
        finally:
            session.close()


# функция, добавляющая id людей в избранные пользователя
def save_favorite(user_id: int, favorites_people_id: int):
    session = get_session()
    if session is None:
        print('Не удалось создать сессию для работы с базой данных')
        return False
    else:
        try:
            result = Favourite(id_user=user_id, id_favorites_people=favorites_people_id)
            session.add(result)
            session.commit()
            return True
        except SQLAlchemyError as e:
            print(f'Произошла ошибка при работе с базой данных: {e}')
            return False
        finally:
            session.close()

# функция, выдающая список понравившихся людей
def show_favorites(user_id: int) -> list[int] | None:
    session = get_session()
    if session is None:
        print('Не удалось создать сессию для работы с базой данных')
        return None
    else:
        try:
            favorites = session.query(Favourite.id_favorites_people).filter(Favourite.id_user == user_id).all()
            return [fav[0] for fav in favorites]
        except SQLAlchemyError as e:
            print(f'Произошла ошибка при работе с базой данных: {e}')
            return None
        finally:
            session.close()

# функция, добавляющая id людей в черный список пользователя
def save_blacklist(user_id: int, bad_people_id: int):
    session = get_session()
    if session is None:
        print('Не удалось создать сессию для работы с базой данных')
        return False
    else:
        try:
            result = Blacklist(id_user=user_id, id_blacklist_people=bad_people_id)
            session.add(result)
            session.commit()
            return True
        except SQLAlchemyError as e:
            print(f'Произошла ошибка при работе с базой данных: {e}')
            return False
        finally:
            session.close()

# функция, выдающая список людей из черного списка
def show_blacklist(user_id: int) -> list[int] | None:
    session = get_session()
    if session is None:
        print('Не удалось создать сессию для работы с базой данных')
        return None
    else:
        try:
            blacklist = session.query(Blacklist.id_blacklist_people).filter(Blacklist.id_user == user_id).all()
            return [bad[0] for bad in blacklist]
        except SQLAlchemyError as e:
            print(f'Произошла ошибка при работе с базой данных: {e}')
            return None
        finally:
            session.close()


# функция для удаления людей из избранных
def delete_favorite_people(user_id: int, favorites_id: int):
    session = get_session()
    if session is None:
        print('Не удалось создать сессию для работы с базой данных')
        return False
    else:
        try:
            delete = session.query(Favourite.id_favorites_people) \
                .filter(Favourite.id_user == user_id, Favourite.id_favorites_people == favorites_id) \
                .delete()
            session.commit()
            return True
        except SQLAlchemyError as e:
            print(f'Произошла ошибка при работе с базой данных: {e}')
            return False
        finally:
            session.close()

# функция для удаления людей из черного списка
def delete_blacklist_people(user_id: int, bad_people_id: int):
    session = get_session()
    if session is None:
        print('Не удалось создать сессию для работы с базой данных')
        return False
    else:
        try:
            delete = session.query(Blacklist.id_blacklist_people) \
                .filter(Blacklist.id_user == user_id, Blacklist.id_blacklist_people == bad_people_id) \
                .delete()
            session.commit()
            return True
        except SQLAlchemyError as e:
            print(f'Произошла ошибка при работе с базой данных: {e}')
            return False
        finally:
            session.close()

# Функция для удаления записей о человеке из таблицы SearchResult после того,
# как пользователь отреагировал на его профиль (пропустил/добавил в избранное/в чс), чтобы избежать дублирования
def delete_from_search(user_id: int, random_human_id: int):
    session = get_session()
    if session is None:
        print('Не удалось создать сессию для работы с базой данных')
        return False
    else:
        try:
            session.query(SearchResult.id_found_people) \
                .filter(SearchResult.id_user == user_id, SearchResult.id_found_people == random_human_id) \
                .delete()
            session.commit()
            return True
        except SQLAlchemyError as e:
            print(f'Произошла ошибка при работе с базой данных: {e}')
            return False
        finally:
            session.close()

# Функция для удаления всех записей в таблице SearchResult при повторном запуске бота,
# чтобы избежать дублирования старых записей
def delete_all_from_search(user_id: int):
    session = get_session()
    if session is None:
        print('Не удалось создать сессию для работы с базой данных')
        return False
    else:
        try:
            session.query(SearchResult.id_found_people).filter(SearchResult.id_user == user_id).delete()
            return True
        except SQLAlchemyError as e:
            print(f'Произошла ошибка при работе с базой данных: {e}')
            return False
        finally:
            session.close()