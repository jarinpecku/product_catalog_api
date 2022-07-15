"""
Threadsafe connection pool for MySQL
"""
import logging
import json
from contextlib import closing
from os import environ

import mysql.connector.pooling
from fastapi import HTTPException

from catalog.models import Product


log = logging.getLogger()


def places(arg_list):
    """
    Vygeneruje string s %s pro vlozeni do SQL query

    Args:
        arg_list (list or tuple):

    Returns:
        str: string s placeholders
    """
    return ('%s,'*len(arg_list))[:-1]


class DB:
    def __init__(self):
        self.__cnxpool = mysql.connector.pooling.MySQLConnectionPool(pool_size=8,
                                                                     host=environ["MYSQL_HOST"],
                                                                     db=environ["MYSQL_DB"],
                                                                     user=environ["MYSQL_USER"],
                                                                     password=environ["MYSQL_PASSWORD"],
                                                                     autocommit=True,
                                                                     )

    def _select_all(self, query, args=()):
        """
        Pusti select v samostatne connection a vrati vysledek

        Args:
            query (str):  query string. Pokud je s pojmenovanýmy parametry %(name)s musí args být dict
            args  (tuple or list or dict): argumenty query

        Returns:
            list of dict

        Raises:
            mysql.connector.Error
        """
        with closing(self.__get_connection()) as cnx, closing(cnx.cursor(dictionary=True)) as cur:
            cur.execute(query, args)
            res = cur.fetchall()
            return res

    def _select_one(self, query, args=()):
        """
        Pusti select v samostatne connection a vrati vysledek

        Args:
            query (str):  query string. Pokud je s pojmenovanýmy parametry %(name)s musí args být dict
            args  (tuple or list or dict): argumenty query

        Returns:
            dict/None

        Raises:
            mysql.connector.Error
        """
        with closing(self.__get_connection()) as cnx, closing(cnx.cursor(dictionary=True)) as cur:
            cur.execute(query, args)
            res = cur.fetchone()
            return res

    def _execute(self, query, args=()):
        """
        Pusti query v samostatne connection a provede commit

        Args:
            query (str):  query string. Pokud je s pojmenovanýmy parametry %(name)s musí args být dict
            args  (tuple or list or dict): argumenty query

        Raises:
            mysql.connector.Error

        Returns:
            int: pocet upravenych radek
        """
        with closing(self.__get_connection()) as cnx, closing(cnx.cursor()) as cur:
            cur.execute(query, args)
            cnx.commit()
            rowcount = cur.rowcount
            return rowcount

    def _insert_many(self, query, seq_of_params):
        """
        Pusti insert query se sekvenci predanych parametru v samostatne connection a provede commit.
        Lze odekorovat run_repeatedly dekoratorem - pokud cur.executemany vyhodi vyjimku, cursor je uzavren
        bez commitu a dekorator tedy muze celou operaci zkusit zopakovat.

        Args:
            query (str):  query string. Pokud je s pojmenovanýmy parametry %(name)s musí args být dict
            seq_of_params (tuple or list or dict): sekvence argumentu

        Raises:
            mysql.connector.Error

        Returns:
            int: pocet upravenych radek
        """
        with closing(self.__get_connection()) as cnx, closing(cnx.cursor()) as cur:
            cur.executemany(query, seq_of_params)
            cnx.commit()
            rowcount = cur.rowcount
            return rowcount

    def __get_connection(self):
        """
        Vrati volnou connection z poolu. Pokud zadna neni, provede sleep a retry.

        Returns:
            mysql.connector.pooling.PooledMySQLConnection

        Raises:
            mysql.connector.errors.PoolError
        """
        return self.__cnxpool.get_connection()


class ProductCatalogDB(DB):
    ACCESS_TOKEN_PARAM_NAME = "access_token"

    def insert_product(self, product: Product):
        params = dict(product)
        insert = "INSERT INTO product (name, description) VALUES (%(name)s, %(description)s) ON DUPLICATE KEY UPDATE id=id"
        rowcount = self._execute(insert, params)
        if not rowcount == 1:
            log.warning("Duplicit product name %s", product.name)

        select = "SELECT id FROM product WHERE name=%(name)s AND description=%(description)s"
        inserted_product = self._select_one(select, params)
        if inserted_product:
            log.info("Product %s successfully inserted under id %d", params, inserted_product["id"])
            return inserted_product["id"]
        else:
            log.error("Product with name %s already exists with different description", product.name)
            raise HTTPException(status_code=409, detail="Product of this name already exists")

    def select_product(self, id: int):
        select = "SELECT id, name, description FROM product WHERE id=%(id)s"
        product = self._select_one(select, dict(id=id))
        if product:
            log.info("Selected product %s", product)
            return product
        else:
            log.warning("Product %d not found", id)
            raise HTTPException(status_code=404, detail="Product not found")

    def update_product(self, id: int, product: Product):
        update = "UPDATE product SET name=%(name)s, description=%(description)s WHERE id=%(id)s"
        rowcount = self._execute(update, dict(id=id, name=product.name, description=product.description))
        if rowcount == 1:
            log.info("Product %d successfully updated", id)
        else:
            log.warning("Product %d not found", id)
            raise HTTPException(status_code=404, detail="Product not found")

    def delete_product(self, id: int):
        delete = "DELETE FROM product WHERE id=%(id)s"
        rowcount = self._execute(delete, dict(id=id))
        if rowcount == 1:
            log.info("Product %d successfully deleted", id)
        else:
            log.warning("Product %d not found", id)
            raise HTTPException(status_code=404, detail="Product not found")

    def list_all_product_ids(self):
        select = "SELECT JSON_ARRAYAGG(id) AS ids FROM product"
        result = self._select_one(select)
        if not result:
            return []
        else:
            return json.loads(result["ids"])

    def insert_product_offers(self, product_id: int, offers: list[dict]):
        for offer in offers:
            offer["product_id"] = product_id

        insert = """INSERT INTO offer (product_id, foreign_id, price, items_in_stock)
                    VALUES (%(product_id)s, %(id)s, %(price)s, %(items_in_stock)s)
                    ON DUPLICATE KEY UPDATE price=VALUES(price), items_in_stock=VALUES(items_in_stock)"""
        rowcount = self._insert_many(insert, offers)
        log.debug("num of offers being inserted: %d, rowcount: %d", len(offers), rowcount)

    def delete_obsolete_product_offers(self, product_id: int, offers: list[dict]):
        ids = [offer["id"] for offer in offers]
        delete = f"DELETE FROM offer WHERE product_id={product_id} AND foreign_id NOT IN ({places(ids)})"
        rowcount = self._execute(delete, ids)
        log.debug("%d offers deleted", rowcount)

    def select_product_offers(self, product_id: int):
        select = "SELECT id AS offer_id, product_id, price, items_in_stock FROM offer WHERE product_id=%(product_id)s"
        offers = self._select_all(select, dict(product_id=product_id))
        return offers

    def select_access_token(self):
        select = 'SELECT value FROM params WHERE name=%(param_name)s'
        token = self._select_one(select, dict(param_name=self.ACCESS_TOKEN_PARAM_NAME))
        if token:
            return token["value"]
        else:
            return None

    def insert_access_token(self, value: str):
        log.debug("value %s", value)
        insert = 'INSERT INTO params VALUES (%(param_name)s, %(value)s) ON DUPLICATE KEY UPDATE name=name'
        rowcount = self._execute(insert, dict(param_name=self.ACCESS_TOKEN_PARAM_NAME, value=value))

        if rowcount == 1:
            log.debug("Access token successfully inserted")
            return value

        log.warning("Access token already exists")
        token = self.select_access_token()

        if not token:
            raise RuntimeError("Can not insert access token")

        return token



