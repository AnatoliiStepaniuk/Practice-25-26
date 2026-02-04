import json
import os
import shutil
import threading
import time
import pytest
import requests
from app import app, DATA_FILE

BASE_URL = "http://127.0.0.1:5051"
BACKUP_FILE = DATA_FILE + ".bak"
API_KEY = os.environ.get("TEST_API_KEY", "secret123")
HEADERS = {}


def _login():
    """Get a JWT token from the /login endpoint."""
    resp = requests.post(f"{BASE_URL}/login", json={"api_key": API_KEY}, timeout=2)
    return resp.json()["token"]


@pytest.fixture(scope="session", autouse=True)
def server():
    """Start the real Flask server in a background thread for the test session."""
    global HEADERS
    if os.path.exists(DATA_FILE):
        shutil.copy2(DATA_FILE, BACKUP_FILE)

    srv = threading.Thread(
        target=lambda: app.run(port=5051, use_reloader=False),
        daemon=True,
    )
    srv.start()

    # Wait until the server is ready
    for _ in range(20):
        try:
            requests.post(f"{BASE_URL}/login", json={"api_key": API_KEY}, timeout=0.5)
            break
        except requests.ConnectionError:
            time.sleep(0.25)

    HEADERS = {"Authorization": f"Bearer {_login()}"}
    yield

    if os.path.exists(BACKUP_FILE):
        shutil.move(BACKUP_FILE, DATA_FILE)


@pytest.fixture(autouse=True)
def cleanup():
    """Reset the data file to an empty list before each test."""
    with open(DATA_FILE, "w") as f:
        json.dump([], f)
    yield


# ---------- Auth ----------

def test_request_without_auth():
    resp = requests.get(f"{BASE_URL}/users")
    assert resp.status_code == 401
    assert "Unauthorized" in resp.json()["error"]


def test_request_with_invalid_token():
    resp = requests.get(f"{BASE_URL}/users", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401


def test_login_with_wrong_key():
    resp = requests.post(f"{BASE_URL}/login", json={"api_key": "wrongkey"})
    assert resp.status_code == 401


def test_login_success():
    resp = requests.post(f"{BASE_URL}/login", json={"api_key": API_KEY})
    assert resp.status_code == 200
    assert "token" in resp.json()


# ---------- GET /users ----------

def test_get_users_empty():
    resp = requests.get(f"{BASE_URL}/users", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_users_returns_created():
    requests.post(f"{BASE_URL}/users", json={"name": "A", "email": "a@a.com", "age": 20}, headers=HEADERS)
    requests.post(f"{BASE_URL}/users", json={"name": "B", "email": "b@b.com", "age": 30}, headers=HEADERS)
    resp = requests.get(f"{BASE_URL}/users", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["name"] == "A"
    assert data[1]["name"] == "B"


# ---------- POST /users ----------

def test_create_user():
    resp = requests.post(f"{BASE_URL}/users", json={"name": "Alice", "email": "alice@test.com", "age": 25}, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == 1
    assert data["name"] == "Alice"
    assert data["email"] == "alice@test.com"
    assert data["age"] == 25


def test_create_user_increments_id():
    requests.post(f"{BASE_URL}/users", json={"name": "A", "email": "a@a.com", "age": 20}, headers=HEADERS)
    resp = requests.post(f"{BASE_URL}/users", json={"name": "B", "email": "b@b.com", "age": 30}, headers=HEADERS)
    assert resp.json()["id"] == 2


def test_create_user_missing_name():
    resp = requests.post(f"{BASE_URL}/users", json={"email": "x@x.com", "age": 20}, headers=HEADERS)
    assert resp.status_code == 400
    assert "name" in resp.json()["error"]


def test_create_user_missing_email():
    resp = requests.post(f"{BASE_URL}/users", json={"name": "X", "age": 20}, headers=HEADERS)
    assert resp.status_code == 400
    assert "email" in resp.json()["error"]


def test_create_user_missing_age():
    resp = requests.post(f"{BASE_URL}/users", json={"name": "X", "email": "x@x.com"}, headers=HEADERS)
    assert resp.status_code == 400
    assert "age" in resp.json()["error"]


def test_create_user_empty_body():
    resp = requests.post(f"{BASE_URL}/users", json={}, headers=HEADERS)
    assert resp.status_code == 400


# ---------- GET /users/<id> ----------

def test_get_user_by_id():
    requests.post(f"{BASE_URL}/users", json={"name": "Alice", "email": "alice@test.com", "age": 25}, headers=HEADERS)
    resp = requests.get(f"{BASE_URL}/users/1", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Alice"


def test_get_user_not_found():
    resp = requests.get(f"{BASE_URL}/users/999", headers=HEADERS)
    assert resp.status_code == 404
    assert "not found" in resp.json()["error"].lower()


# ---------- PUT /users/<id> ----------

def test_update_user_name():
    requests.post(f"{BASE_URL}/users", json={"name": "Alice", "email": "a@a.com", "age": 25}, headers=HEADERS)
    resp = requests.put(f"{BASE_URL}/users/1", json={"name": "Alice Updated"}, headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Alice Updated"
    assert data["email"] == "a@a.com"
    assert data["age"] == 25


def test_update_user_email():
    requests.post(f"{BASE_URL}/users", json={"name": "Alice", "email": "a@a.com", "age": 25}, headers=HEADERS)
    resp = requests.put(f"{BASE_URL}/users/1", json={"email": "new@a.com"}, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["email"] == "new@a.com"


def test_update_user_age():
    requests.post(f"{BASE_URL}/users", json={"name": "Alice", "email": "a@a.com", "age": 25}, headers=HEADERS)
    resp = requests.put(f"{BASE_URL}/users/1", json={"age": 30}, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["age"] == 30


def test_update_user_all_fields():
    requests.post(f"{BASE_URL}/users", json={"name": "Alice", "email": "a@a.com", "age": 25}, headers=HEADERS)
    resp = requests.put(f"{BASE_URL}/users/1", json={"name": "Bob", "email": "bob@b.com", "age": 40}, headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Bob"
    assert data["email"] == "bob@b.com"
    assert data["age"] == 40


def test_update_user_not_found():
    resp = requests.put(f"{BASE_URL}/users/999", json={"name": "X"}, headers=HEADERS)
    assert resp.status_code == 404


def test_update_user_empty_body():
    requests.post(f"{BASE_URL}/users", json={"name": "Alice", "email": "a@a.com", "age": 25}, headers=HEADERS)
    resp = requests.put(f"{BASE_URL}/users/1", json={}, headers=HEADERS)
    assert resp.status_code == 400


# ---------- DELETE /users/<id> ----------

def test_delete_user():
    requests.post(f"{BASE_URL}/users", json={"name": "Alice", "email": "a@a.com", "age": 25}, headers=HEADERS)
    resp = requests.delete(f"{BASE_URL}/users/1", headers=HEADERS)
    assert resp.status_code == 200
    assert "deleted" in resp.json()["message"].lower()
    # Verify gone
    assert requests.get(f"{BASE_URL}/users/1", headers=HEADERS).status_code == 404


def test_delete_user_not_found():
    resp = requests.delete(f"{BASE_URL}/users/999", headers=HEADERS)
    assert resp.status_code == 404


# ---------- Full CRUD flow ----------

def test_full_crud_flow():
    # Create
    r = requests.post(f"{BASE_URL}/users", json={"name": "Test", "email": "t@t.com", "age": 20}, headers=HEADERS)
    assert r.status_code == 201
    user_id = r.json()["id"]

    # Read
    r = requests.get(f"{BASE_URL}/users/{user_id}", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["name"] == "Test"

    # Update
    r = requests.put(f"{BASE_URL}/users/{user_id}", json={"name": "Updated", "age": 99}, headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["name"] == "Updated"
    assert r.json()["age"] == 99

    # Delete
    r = requests.delete(f"{BASE_URL}/users/{user_id}", headers=HEADERS)
    assert r.status_code == 200

    # Verify deleted
    r = requests.get(f"{BASE_URL}/users/{user_id}", headers=HEADERS)
    assert r.status_code == 404
