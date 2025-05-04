from sqlalchemy import create_engine
import psycopg2
from psycopg2 import sql
import database.orm_models

def initialize_db(DSN):
    engine = create_engine(DSN)
    try:
        conn = engine.connect()
        conn.close()
        return True
    except:
        return False

def create_db(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT):
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True  # Включаем автокоммит для создания базы данных
        cursor = conn.cursor()

        # Формируем SQL запрос для создания базы данных
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))

        # Закрываем соединение
        cursor.close()
        conn.close()
        return True
    except:
        return False

def create_tables(engine):
    # database.orm_models.Base.metadata.drop_all(engine) # Раскомментировать для очистки таблиц
    database.orm_models.Base.metadata.create_all(engine)



