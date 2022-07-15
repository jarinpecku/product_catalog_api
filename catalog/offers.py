from os import environ
import requests
import logging

from catalog.db import ProductCatalogDB
from catalog.models import Product


log = logging.getLogger()


class OffersApi:

    def __init__(self, db: ProductCatalogDB):
        self._base_url = environ["OFFERS_API_BASE_URL"]

        token = db.select_access_token()
        if token:
            log.debug("Access token %s found", token)
        else:
            log.debug("Requesting new access token")
            token = self._auth()
            token = db.insert_access_token(token)

        self._session = requests.Session()
        self._session.headers.update(dict(Bearer=token))

    def _auth(self) -> str:
        response = requests.post(url=f"{self._base_url}/auth")
        response.raise_for_status()
        token = response.json()["access_token"]
        log.debug("New access token %s received", token)
        return token

    def register_product(self, product: Product):
        response = self._session.post(url=f"{self._base_url}/products/register", json=dict(product))
        response.raise_for_status()

    def get_offers(self, id: int):
        response = self._session.get(url=f"{self._base_url}/products/{id}/offers")
        response.raise_for_status()
        return response.json()


