import logging
import json
import datetime
from contextlib import closing
from os import environ
from typing import Iterable

import mysql.connector.pooling
from fastapi import HTTPException

from catalog.models import Product
from catalog.offers import get_access_token


log = logging.getLogger()


def places(arg_list: list) -> str:
    """
    Generates string with placeholders
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

    def _select_all(self, query: str, args: Iterable = ()) -> list[dict]:
        """
        Runs select in separated connection and fetches all result.

        Args:
            query      (str): query string
            args  (Iterable): query arguments

        Returns:
            list of dict: each dict represents one selected record

        Raises:
            mysql.connector.Error
        """
        with closing(self.__get_connection()) as cnx, closing(cnx.cursor(dictionary=True)) as cur:
            cur.execute(query, args)
            res = cur.fetchall()
            return res

    def _select_one(self, query: str, args: Iterable = ()) -> dict | None:
        """
        Runs select in separated connection and fetches one result.

        Args:
            query      (str): query string
            args  (Iterable): query arguments

        Returns:
            dict/None

        Raises:
            mysql.connector.Error
        """
        with closing(self.__get_connection()) as cnx, closing(cnx.cursor(dictionary=True)) as cur:
            cur.execute(query, args)
            res = cur.fetchone()
            return res

    def _execute(self, query: str, args: Iterable = ()) -> int:
        """
        Runs query in separated connection and returns a number of affected rows

        Args:
            query      (str): query string
            args  (Iterable): query arguments

        Raises:
            mysql.connector.Error

        Returns:
            int: number of affected rows
        """
        with closing(self.__get_connection()) as cnx, closing(cnx.cursor()) as cur:
            cur.execute(query, args)
            cnx.commit()
            rowcount = cur.rowcount
            return rowcount

    def _insert_many(self, query: str, seq_of_params: Iterable) -> int:
        """
        Runs insert query in separated connection. Accepts iterable of multiple query params

        Args:
            query              (str): query string
            seq_of_params (Iterable): sequence of query arguments

        Raises:
            mysql.connector.Error

        Returns:
            int: number of affected rows
        """
        with closing(self.__get_connection()) as cnx, closing(cnx.cursor()) as cur:
            cur.executemany(query, seq_of_params)
            cnx.commit()
            rowcount = cur.rowcount
            return rowcount

    def __get_connection(self):
        """
        Returns connection from pool

        Returns:
            mysql.connector.pooling.PooledMySQLConnection

        Raises:
            mysql.connector.errors.PoolError
        """
        return self.__cnxpool.get_connection()


class ProductCatalogDB(DB):
    def __init__(self):
        """
        Check DB for access token. If not found a new one is requested from external API and saved into DB.
        If an existing access token is found in the DB does the URL check. If the url from DB does not match
        the external API url taken from env var the application configuration is not valid and app can not be started.
        """
        super().__init__()

        url = environ['OFFERS_API_BASE_URL']
        token_dict = self._select_access_token()
        if token_dict:
            msg = f"Found access token belongs to service {token_dict['url']} but given service is {url}"
            assert token_dict['url'] == url, msg
        else:
            token_dict = self._insert_access_token(get_access_token(), url)

        self._service_id = token_dict['id']
        self._access_token = token_dict['access_token']

    @property
    def access_token(self):
        return self._access_token

    def insert_product(self, product: Product) -> int:
        """
        Inserts given product into product table.
        """
        params = dict(product)
        params |= dict(service_id=self._service_id)
        insert = """INSERT INTO product (service_id, name, description) 
                    VALUES (%(service_id)s, %(name)s, %(description)s) ON DUPLICATE KEY UPDATE id=id"""
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

    def select_product(self, id: int) -> dict:
        """
        Selects product of given id from DB.

        raises:
            HTTPException: Product not found
        """
        select = "SELECT id, name, description FROM product WHERE id=%(id)s"
        product = self._select_one(select, dict(id=id))
        if product:
            log.info("Selected product %s", product)
            return product
        else:
            log.warning("Product %d not found", id)
            raise HTTPException(status_code=404, detail="Product not found")

    def update_product(self, id: int, product: Product) -> dict:
        """
        Update product of given id.

        raises:
            HTTPException: Product not found
        """
        update = "UPDATE product SET name=%(name)s, description=%(description)s WHERE id=%(id)s"
        rowcount = self._execute(update, dict(id=id, name=product.name, description=product.description))
        if rowcount == 1:
            log.info("Product %d successfully updated", id)
        else:
            log.warning("Product %d not found", id)
            raise HTTPException(status_code=404, detail="Product not found")
        product.id = id
        return dict(product)

    def delete_product(self, id: int) -> None:
        """
        Deletes product of given id from DB.

        raises:
            HTTPException: Product not found
        """
        delete = "DELETE FROM product WHERE id=%(id)s"
        rowcount = self._execute(delete, dict(id=id))
        if rowcount == 1:
            log.info("Product %d successfully deleted", id)
        else:
            log.warning("Product %d not found", id)
            raise HTTPException(status_code=404, detail="Product not found")

    def list_all_product_ids(self) -> list[int]:
        """
        Returns all product ids.
        """
        select = "SELECT JSON_ARRAYAGG(id) AS ids FROM product"
        ids = self._select_one(select)["ids"]
        return json.loads(ids) if ids else []

    def insert_product_offers(self, product_id: int, offers: list[dict]) -> None:
        """
        Insert all given offers of specified product into DB.
        If offer already exists updates the items_in_stock column.
        """
        for offer in offers:
            offer["product_id"] = product_id

        insert = """INSERT INTO offer (product_id, foreign_id, items_in_stock)
                    VALUES (%(product_id)s, %(id)s, %(items_in_stock)s)
                    ON DUPLICATE KEY UPDATE items_in_stock=VALUES(items_in_stock)"""
        rowcount = self._insert_many(insert, offers)
        log.debug("num of offers being inserted: %d, rowcount: %d", len(offers), rowcount)

    def delete_obsolete_product_offers(self, product_id: int, offers: list[dict]) -> None:
        """
        Deletes all offers of specified product except given offer ids.
        """
        ids = [offer["id"] for offer in offers]
        delete = f"DELETE FROM offer WHERE product_id={product_id} AND foreign_id NOT IN ({places(ids)})"
        rowcount = self._execute(delete, ids)
        log.debug("%d offers deleted", rowcount)

    def select_product_offers(self, product_id: int, on_stock: bool = True) -> list[dict]:
        """
        Returns offers of specified product. It takes the latest known price.
        If a offer does not have any price return it anyway.
        It is needed for the computation of prices to be inserted.
        """
        min_stock = 1 if on_stock else 0
        select = """SELECT 
                        o.id AS offer_id,
                        o.product_id AS product_id,
                        o.foreign_id AS foreign_id,
                        p.price AS price,
                        o.items_in_stock AS items_in_stock 
                    FROM offer AS o LEFT JOIN price AS p ON o.id=p.offer_id
                        AND o.product_id=%(product_id)s 
                        AND p.id=(SELECT max(id) FROM price WHERE offer_id=o.id)
                    WHERE o.items_in_stock >= %(min_stock)s"""
        return self._select_all(select, dict(product_id=product_id, min_stock=min_stock))

    def insert_prices(self, prices: list) -> None:
        """
        Inserts given prices into price table.
        """
        insert = "INSERT INTO price (offer_id, price) VALUES (%(offer_id)s, %(price)s)"
        rowcount = self._insert_many(insert, prices)
        if rowcount > 0:
            log.debug("%d prices inserted", rowcount)

    def select_offer_prices(self, offer_id: int, start: datetime.datetime, end: datetime.datetime) -> list[dict]:
        """
        Select prices for specified offer with times when they were applied.
        """
        start = datetime.date(year=2000, month=1, day=1).isoformat() if start is None else start
        end = datetime.datetime.now().isoformat() if end is None else end
        select = """SELECT price, created_at AS valid_from FROM price 
                    WHERE offer_id=%(offer_id)s AND created_at > %(start)s AND created_at < %(end)s"""
        params = dict(offer_id=offer_id, start=start, end=end)
        return self._select_all(select, params)

    def _select_access_token(self) -> dict:
        """
        Selects access token with corresponding external API url from DB.
        """
        select = 'SELECT id, access_token, url FROM service'
        response = self._select_all(select)
        if res_len := len(response) == 1:
            return response[0]
        elif res_len == 0:
            return None
        else:
            raise RuntimeError("More than one access tokens found!")

    def _insert_access_token(self, access_token: str, url: str) -> dict:
        """
        Inserts given access token with url used for its registration into DB.
        """
        insert = """INSERT INTO service (access_token, url) 
                    VALUES (%(access_token)s, %(url)s) ON DUPLICATE KEY UPDATE id=id"""
        rowcount = self._execute(insert, dict(access_token=access_token, url=url))
        assert rowcount == 1, "Can not insert access token into DB"
        log.warning("Access successfully inserted")
        return self._select_access_token()
