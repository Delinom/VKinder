import sqlalchemy
from sqlalchemy.orm import sessionmaker
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from users_database_models import Users, SearchResult, Favourites, Blacklist, create_table
import configparser


config = configparser.ConfigParser()
config.read('settings.ini')
vk_token = config['Tokens']['vk_token']
dsn = config['DSN']['dsn']

# авторизация с помощью токена
authorization  = vk_api.VkApi(token=vk_token)
long_poll = VkLongPoll(authorization)
vk = authorization.get_api()
group_id = 230213428

# создание сессии
engine = sqlalchemy.create_engine(dsn)
create_table(engine)
Session = sessionmaker(bind=engine)
session = Session()

# функция, записывающая id пользователей в базу данных
def save_userid(user_id: int):
    existing_user = session.query(Users).filter(Users.id_vk == user_id).first()
    try:
        if existing_user is None:
            new_user = Users(id_vk=user_id)
            session.add(new_user)
            session.commit()
            print(f'В базу данных добавлен новый пользователь {new_user}.')
        else:
            print(f'Пользователь {user_id} уже есть в базе данных.')

    except Exception as e:
        print(f'Ошибка при добавлении пользователя {e}')

# получение событий и id пользователей
for event in long_poll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        save_userid(event.user_id)


# функция, записывающая id найденных людей
def save_search_result():
    pass

# функция, добавляющая id людей в избранные пользователя
def save_favorite():
    pass

# функция, записывающая id людей в черный список пользователя
def save_blacklist():
    pass