import requests

from common import insert_into_db, clear_db, BASE_URL


def teardown_function():
    clear_db()


def test_not_found():
    response = requests.delete(url=f"{BASE_URL}/product/42")
    assert response.status_code == 404
    assert response.json() == dict(detail="Product not found")


def test_success():
    insert_into_db([f"INSERT INTO product (id, service_id, name, description) VALUES (42, 1, 'name', 'description')", ])
    response = requests.delete(url=f"{BASE_URL}/product/42")
    assert response.status_code == 200
    assert response.json() == None

