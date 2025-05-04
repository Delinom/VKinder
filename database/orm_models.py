from sqlalchemy import ForeignKey, Column, String, Integer, DateTime
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id_vk = Column(Integer, primary_key=True)
    token = Column(String(length=300), nullable=False)
    token_expire = Column(DateTime, nullable=False)
    first_name = Column(String(length=40), nullable=False)
    last_name = Column(String(length=60), nullable=False)
    sex = Column(Integer, nullable=False)

    search_result = relationship('SearchResult', back_populates='user')
    favorites_people = relationship('Favourite', back_populates='user')
    blacklist_people = relationship('Blacklist', back_populates='user')


class SearchResult(Base):
    __tablename__ = 'search_result'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_user = Column(Integer, ForeignKey('users.id_vk'), nullable=False)
    id_found_people  = Column(Integer, nullable=False)

    user = relationship('User', back_populates='search_result')


class Favourite(Base):
    __tablename__ = 'favourites'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_user = Column(Integer, ForeignKey('users.id_vk'), nullable=False)
    id_favorites_people = Column(Integer)

    user = relationship('User', back_populates='favorites_people')


class Blacklist(Base):
    __tablename__ = 'blacklist'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_user = Column(Integer, ForeignKey('users.id_vk'), nullable=False)
    id_blacklist_people = Column(Integer)

    user = relationship('User', back_populates='blacklist_people')
