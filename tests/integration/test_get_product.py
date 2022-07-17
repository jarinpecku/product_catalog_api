import requests

from common import insert_into_db, clear_db, BASE_URL


def teardown_function():
    clear_db()


def test_not_found():
    response = requests.get(url=f"{BASE_URL}/product/42")
    assert response.status_code == 404
    assert response.json() == dict(detail="Product not found")


def test_success():
    product = dict(id=42, name="pivo", description="Velkopopovicky Kozel")
    insert_into_db([f"INSERT INTO product (id, service_id, name, description) "
                    f"VALUES ('{product['id']}', 1, '{product['name']}', '{product['description']}')", ])
    response = requests.get(url=f"{BASE_URL}/product/42", json=product)
    assert response.status_code == 200
    assert response.json() == product
