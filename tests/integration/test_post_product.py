import requests

from common import insert_into_db, clear_db, BASE_URL


def teardown_function():
    clear_db()


def test_success():
    product = dict(name="pivo", description="Velkopopovicky Kozel")
    response = requests.post(url=f"{BASE_URL}/product", json=product)
    assert response.status_code == 201
    inserted_product = response.json()
    assert type(inserted_product.pop("id")) is int
    assert inserted_product == product


def test_already_inserted():
    product = dict(name="pivo", description="Velkopopovicky Kozel")
    insert_into_db([f"INSERT INTO product (service_id, name, description) VALUES (1, '{product['name']}', '{product['description']}')",])
    response = requests.post(url=f"{BASE_URL}/product", json=product)
    assert response.status_code == 201
    inserted_product = response.json()
    assert type(inserted_product.pop("id")) is int
    assert inserted_product == product


def test_conflict():
    product = dict(name="pivo", description="Velkopopovicky Kozel")
    insert_into_db([f"INSERT INTO product (service_id, name, description) VALUES (1, '{product['name']}', 'different description')",])
    response = requests.post(url=f"{BASE_URL}/product", json=product)
    assert response.status_code == 409
    assert response.json() == dict(detail="Product of this name already exists")
