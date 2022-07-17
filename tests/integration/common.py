import mysql.connector


BASE_URL = "http://127.0.0.1:8000"
MYSQL_PASSWORD = "secret"
MYSQL_USER = "root"
MYSQL_DB = "product_catalog_db"
MYSQL_HOST = "localhost"

db_cnx = mysql.connector.connect(user=MYSQL_USER, database=MYSQL_DB, password=MYSQL_PASSWORD, host=MYSQL_HOST)


def insert_into_db(query_list):
    cursor = db_cnx.cursor()
    for query in query_list:
        cursor.execute(query)
        db_cnx.commit()


def clear_db():
    cursor = db_cnx.cursor()
    cursor.execute('DELETE FROM product')
    db_cnx.commit()


