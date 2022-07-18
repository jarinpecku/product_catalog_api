import requests

from common import insert_into_db, clear_db, BASE_URL


def teardown_function():
    clear_db()


def test_no_offers_found():
    response = requests.get(url=f"{BASE_URL}/product/42/offers")
    assert response.status_code == 200
    assert response.json() == []


def test_success_on_stock():
    sqls = ["INSERT INTO product VALUES (42, 1, 'name', 'description')",
            "INSERT INTO offer VALUES (1, 42, 11, 5), (2, 42, 12, 0)",
            "INSERT INTO price (offer_id, price) VALUES (1, 13), (1, 17), (2, 14), (2, 11)"]
    insert_into_db(sqls)
    response = requests.get(url=f"{BASE_URL}/product/42/offers", params=dict(on_stock=True))
    assert response.status_code == 200
    assert response.json() == [dict(offer_id=1, product_id=42, price=17, items_in_stock=5)]


def test_success_all():
    sqls = ["INSERT INTO product VALUES (42, 1, 'name', 'description')",
            "INSERT INTO offer VALUES (1, 42, 11, 5), (2, 42, 12, 0)",
            "INSERT INTO price (offer_id, price) VALUES (1, 13), (1, 17), (2, 14), (2, 11)"]
    insert_into_db(sqls)
    response = requests.get(url=f"{BASE_URL}/product/42/offers", params=dict(on_stock=False))
    assert response.status_code == 200
    assert response.json() == [dict(offer_id=1, product_id=42, price=17, items_in_stock=5),
                               dict(offer_id=2, product_id=42, price=11, items_in_stock=0)]