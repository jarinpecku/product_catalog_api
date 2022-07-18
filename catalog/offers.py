from os import environ
import requests
import logging

from catalog.models import Product


log = logging.getLogger()


class OffersApi:

    def __init__(self, access_token: str):
        """
        Takes base url from env var and creates session with given access token.
        """
        self._base_url = environ["OFFERS_API_BASE_URL"]
        self._session = requests.Session()
        self._session.headers.update(dict(Bearer=access_token))

    def register_product(self, product: Product) -> None:
        """
        Registers given product in external offers API.
        """
        response = self._session.post(url=f"{self._base_url}/products/register", json=dict(product))
        response.raise_for_status()

    def get_offers(self, id: int) -> list[dict]:
        """
        Gets offers for registered product from external offers API.
        """
        response = self._session.get(url=f"{self._base_url}/products/{id}/offers")
        response.raise_for_status()
        return response.json()


def get_access_token() -> str:
    """
    Registers service and returns access token.
    It is not a part of OffersApi class because it needs to be called before OfferApi instance creation.
    """
    log.debug("Requesting new access token")
    response = requests.post(url=f"{environ['OFFERS_API_BASE_URL']}/auth")
    response.raise_for_status()
    access_token = response.json()["access_token"]
    log.debug("New access token %s received", access_token)
    return access_token
