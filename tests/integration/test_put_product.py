import requests

from common import insert_into_db, clear_db, BASE_URL


def teardown_function():
    clear_db()


def test_not_found():
    product = dict(name="pivo", description="Velkopopovicky Kozel")
    response = requests.put(url=f"{BASE_URL}/product/42", json=product)
    assert response.status_code == 404
    assert response.json() == dict(detail="Product not found")


def test_success():
    product = dict(name="pivo", description="Velkopopovicky Kozel")
    insert_into_db([f"INSERT INTO product (id, service_id, name, description) VALUES (42, 1, 'old_name', 'old description')", ])
    response = requests.put(url=f"{BASE_URL}/product/42", json=product)
    assert response.status_code == 200
    product["id"] = 42
    assert response.json() == product
