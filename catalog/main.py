import sys
import logging
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks, status
from fastapi_utils.tasks import repeat_every
from pydantic import BaseModel

from catalog.db import ProductCatalogDB
from catalog.offers import OffersApi
from catalog.models import Product, ProductNoId, product_not_found_response, product_conflict_response
from catalog.models import delete_response, list_of_offers, prices
from catalog.common import compute_prices_to_insert, calculate_growth, cleanup_offers


log = logging.getLogger()
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.DEBUG)
log.addHandler(stream_handler)


app = FastAPI(title="Product aggregator microservice",
              description="REST API JSON Python microservice which allows users to browse a product catalog "
                          "and which automatically updates prices from the offer service.",
              version="0.1.0",)
db = ProductCatalogDB()
offers_api = OffersApi(db.access_token)


@app.get("/product/{id}", response_model=Product, responses=product_not_found_response)
def get_product(id: int) -> dict:
    return db.select_product(id)


@app.post("/product", status_code=status.HTTP_201_CREATED, response_model=Product, responses=product_conflict_response)
def post_product(product: ProductNoId, backgroud_tasks: BackgroundTasks) -> dict:
    id = db.insert_product(product)
    backgroud_tasks.add_task(register_product, product)
    product_dict = dict(product)
    product_dict["id"] = id
    return product_dict


@app.put("/product/{id}", response_model=Product, responses=product_not_found_response)
def put_product(id: int, product: ProductNoId) -> dict:
    return db.update_product(id, product)


@app.delete("/product/{id}", responses=delete_response)
def delete_product(id: int):
    db.delete_product(id)


@app.get("/product/{id}/offers", responses=list_of_offers)
def get_product_offers(id: int, on_stock: bool = True) -> list[dict]:
    # select_product_offers function returns more than API caller= should see - we have to clean the returned data
    return cleanup_offers(db.select_product_offers(id, on_stock))


@app.get("/offer/{id}/prices", responses=prices)
def get_offer_prices(id: int, start: datetime = None, end: datetime = None) -> dict:
    prices = db.select_offer_prices(id, start, end)
    growth = calculate_growth(prices)
    return dict(prices=prices, growth=growth)


@app.on_event("startup")
@repeat_every(seconds=60)
def update_offers():
    """
    Periodic task to update all offers.
    """
    log.debug("updating offers")
    try:
        _update_offers()
    except Exception as err:
        log.error("Error: %r", err)
    log.debug("offers updated")


def _update_offers():
    """
    First we have to list all products.
    Then for each product:
        - get new offers from API
        - insert new offers into DB, update stock
        - delete obsolete offers
        - get all actual product offers
        - compute prices to be inserted into DB by comparing actual product offers with offers from API
        - insert computed prices into DB
    """
    product_ids = db.list_all_product_ids()
    for product_id in product_ids:
        api_offers = offers_api.get_offers(product_id)
        db.insert_product_offers(product_id, api_offers)
        db.delete_obsolete_product_offers(product_id, api_offers)
        db_offers = db.select_product_offers(product_id)
        prices_to_insert = compute_prices_to_insert(api_offers, db_offers)
        db.insert_prices(prices_to_insert)


def register_product(product: Product):
    offers_api.register_product(product)
