import requests

from common import insert_into_db, clear_db, BASE_URL


def teardown_function():
    clear_db()


def test_not_found():
    response = requests.get(url=f"{BASE_URL}/offer/42/prices")
    assert response.status_code == 200
    assert response.json() == dict(prices=[], growth=None)


def test_success_default_params():
    sqls = ["INSERT INTO product VALUES (42, 1, 'name', 'description')",
            "INSERT INTO offer VALUES (7, 42, 11, 5)",
            "INSERT INTO price (offer_id, price, created_at) "
            "VALUES (7, 13, '2022-01-01'), (7, 17, '2022-01-02'), (7, 14, '2022-01-03'), (7, 11, '2022-01-04')"]
    insert_into_db(sqls)
    response = requests.get(url=f"{BASE_URL}/offer/7/prices")
    assert response.status_code == 200
    prices = [dict(price=13, valid_from='2022-01-01T00:00:00'),
              dict(price=17, valid_from='2022-01-02T00:00:00'),
              dict(price=14, valid_from='2022-01-03T00:00:00'),
              dict(price=11, valid_from='2022-01-04T00:00:00')]
    assert response.json() == dict(prices=prices, growth=-15.38)

def test_success_time_frame():
    sqls = ["INSERT INTO product VALUES (42, 1, 'name', 'description')",
            "INSERT INTO offer VALUES (7, 42, 11, 5)",
            "INSERT INTO price (offer_id, price, created_at) "
            "VALUES (7, 13, '2022-01-01'), (7, 17, '2022-01-02'), (7, 14, '2022-01-03'), (7, 11, '2022-01-04')"]
    insert_into_db(sqls)
    params = dict(start="2022-01-01T12:00:00", end="2022-01-03T12:00:00")
    response = requests.get(url=f"{BASE_URL}/offer/7/prices", params=params)
    assert response.status_code == 200
    prices = [dict(price=17, valid_from='2022-01-02T00:00:00'), dict(price=14, valid_from='2022-01-03T00:00:00')]
    assert response.json() == dict(prices=prices, growth=-17.65)
