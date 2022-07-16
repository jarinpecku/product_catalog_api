import sys
import logging

from fastapi import FastAPI, BackgroundTasks, status
from fastapi_utils.tasks import repeat_every

from catalog.db import ProductCatalogDB
from catalog.offers import OffersApi
from catalog.models import Product


log = logging.getLogger()
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.DEBUG)
log.addHandler(stream_handler)


app = FastAPI()
db = ProductCatalogDB()
offers_api = OffersApi(db.access_token)


@app.get("/product/{id}")
def get_product(id: int):
    return db.select_product(id)


@app.post("/product", status_code=status.HTTP_201_CREATED)
def post_product(product: Product, backgroud_tasks: BackgroundTasks) -> dict:
    product.id = db.insert_product(product)
    backgroud_tasks.add_task(register_product, product)
    return dict(product)


@app.put("/product/{id}")
def put_product(id: int, product: Product):
    return db.update_product(id, product)


@app.delete("/product/{id}")
def delete_product(id: int):
    return db.delete_product(id)


@app.get("/product/{id}/offers")
def get_product_offers(id: int):
    return db.select_product_offers(id)


@app.on_event("startup")
@repeat_every(seconds=10)
def update_offers():
    log.debug("updating offers")
    try:
        product_ids = db.list_all_product_ids()
        for product_id in product_ids:
            offers = offers_api.get_offers(product_id)
            db.insert_product_offers(product_id, offers)
            db.delete_obsolete_product_offers(product_id, offers)
    except Exception as err:
        log.error("Error: %r", err)
    log.debug("offers updated")


def register_product(product: Product):
    offers_api.register_product(product)
