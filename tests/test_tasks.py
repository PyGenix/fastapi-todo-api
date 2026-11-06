import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def login(email="aina@example.com", password="password123"):
    client.post("/auth/register", json={"email": email, "password": password})
    r = client.post("/auth/login", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_create_and_list_tasks():
    headers = login()
    client.post("/tasks", json={"title": "Finish FYP chapter 3"}, headers=headers)
    r = client.get("/tasks", headers=headers)
    assert r.status_code == 200
    assert [t["title"] for t in r.json()] == ["Finish FYP chapter 3"]


def test_users_cannot_see_each_others_tasks():
    a = login("a@example.com")
    b = login("b@example.com")
    task_id = client.post("/tasks", json={"title": "secret"}, headers=a).json()["id"]
    assert client.get("/tasks", headers=b).json() == []
    assert client.patch(f"/tasks/{task_id}", json={"done": True}, headers=b).status_code == 404


def test_filter_done():
    headers = login()
    t = client.post("/tasks", json={"title": "one"}, headers=headers).json()
    client.post("/tasks", json={"title": "two"}, headers=headers)
    client.patch(f"/tasks/{t['id']}", json={"done": True}, headers=headers)
    assert len(client.get("/tasks?done=true", headers=headers).json()) == 1
