from os import environ
import requests
import logging

from catalog.models import Product


log = logging.getLogger()


class OffersApi:

    def __init__(self, access_token: str):
        self._base_url = environ["OFFERS_API_BASE_URL"]
        self._session = requests.Session()
        self._session.headers.update(dict(Bearer=access_token))

    def register_product(self, product: Product):
        response = self._session.post(url=f"{self._base_url}/products/register", json=dict(product))
        response.raise_for_status()

    def get_offers(self, id: int):
        response = self._session.get(url=f"{self._base_url}/products/{id}/offers")
        response.raise_for_status()
        return response.json()


def get_access_token() -> str:
    log.debug("Requesting new access token")
    response = requests.post(url=f"{environ['OFFERS_API_BASE_URL']}/auth")
    response.raise_for_status()
    access_token = response.json()["access_token"]
    log.debug("New access token %s received", access_token)
    return access_token


