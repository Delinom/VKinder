import psycopg2
import sqlalchemy as sql
from sqlalchemy import ForeignKey, ARRAY
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'

    id_vk = sql.Column(sql.Integer)
    token = sql.Column(sql.String(length=256))
    first_name = sql.Column(sql.String(length=40), nullable=False)
    last_name = sql.Column(sql.String(length=60), nullable=False)
    sex = sql.Column(sql.String(length=20), nullable=False)

    search_result = relationship('SearchResult', back_populates='user')
    favorites_people = relationship('Favourites', back_populates='user')
    blacklist_people = relationship('Blacklist', back_populates='user')


class SearchResult(Base):
    __tablename__ = 'search_result'

    id_user = sql.Column(sql.Integer, ForeignKey('users.id_vk'), nullable=False)
    id_found_people  = sql.Column(sql.ARRAY(sql.Integer))

    user = relationship('Users', back_populates='search_result')


class Favourites(Base):
    __tablename__ = 'favourites'

    id_user = sql.Column(sql.Integer, ForeignKey('users.id_vk'), nullable=False)
    id_favorites_people = sql.Column(sql.Intger)

    user = relationship('Users', back_populates='favorites_people')


class Blacklist(Base):
    __tabelename__ = 'blacklist'

    id_user = sql.Column(sql.Integer, ForeignKey('users.id_vk'), nullable=False)
    id_blacklist_people = sql.Column(sql.Integer)

    user = relationship('Users', back_populates='blacklist_people')


def create_table(engine):
    Base.metadata.create_all(engine)
