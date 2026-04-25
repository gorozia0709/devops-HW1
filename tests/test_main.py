import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from main import app, reset_store


@pytest.fixture(autouse=True)
def clean_state():
    reset_store()
    yield


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def add_task(client, title, priority="medium"):
    return client.post("/api/tasks", json={"title": title, "priority": priority})



def test_homepage_loads(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Get things" in res.data


def test_create_task_returns_201(client):
    res = add_task(client, "Buy groceries")
    assert res.status_code == 201


def test_create_task_has_correct_fields(client):
    res = add_task(client, "Buy groceries", "high")
    data = res.get_json()
    assert data["title"] == "Buy groceries"
    assert data["priority"] == "high"
    assert data["done"] is False
    assert "id" in data


def test_create_task_without_title_returns_400(client):
    res = client.post("/api/tasks", json={"priority": "low"})
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_create_task_with_blank_title_returns_400(client):
    res = client.post("/api/tasks", json={"title": "   "})
    assert res.status_code == 400


def test_each_task_gets_a_unique_id(client):
    id1 = add_task(client, "Task A").get_json()["id"]
    id2 = add_task(client, "Task B").get_json()["id"]
    assert id1 != id2



def test_list_starts_empty(client):
    data = client.get("/api/tasks").get_json()
    assert data["tasks"] == []
    assert data["total"] == 0


def test_list_returns_all_tasks(client):
    add_task(client, "Task A")
    add_task(client, "Task B")
    add_task(client, "Task C")
    data = client.get("/api/tasks").get_json()
    assert data["total"] == 3


def test_filter_active_tasks(client):
    add_task(client, "Pending task")
    task_id = add_task(client, "Done task").get_json()["id"]
    client.put(f"/api/tasks/{task_id}", json={"done": True})

    res = client.get("/api/tasks?done=false").get_json()
    assert res["total"] == 1
    assert res["tasks"][0]["title"] == "Pending task"


def test_filter_completed_tasks(client):
    add_task(client, "Pending task")
    task_id = add_task(client, "Done task").get_json()["id"]
    client.put(f"/api/tasks/{task_id}", json={"done": True})

    res = client.get("/api/tasks?done=true").get_json()
    assert res["total"] == 1
    assert res["tasks"][0]["done"] is True



def test_mark_task_as_done(client):
    task_id = add_task(client, "Exercise").get_json()["id"]
    res = client.put(f"/api/tasks/{task_id}", json={"done": True})
    assert res.status_code == 200
    assert res.get_json()["done"] is True


def test_update_task_title(client):
    task_id = add_task(client, "Old title").get_json()["id"]
    res = client.put(f"/api/tasks/{task_id}", json={"title": "New title"})
    assert res.get_json()["title"] == "New title"


def test_update_task_priority(client):
    task_id = add_task(client, "Some task", "low").get_json()["id"]
    res = client.put(f"/api/tasks/{task_id}", json={"priority": "high"})
    assert res.get_json()["priority"] == "high"


def test_update_nonexistent_task_returns_404(client):
    res = client.put("/api/tasks/999", json={"done": True})
    assert res.status_code == 404


def test_update_with_empty_title_returns_400(client):
    task_id = add_task(client, "Some task").get_json()["id"]
    res = client.put(f"/api/tasks/{task_id}", json={"title": ""})
    assert res.status_code == 400


def test_update_done_with_non_boolean_returns_400(client):
    task_id = add_task(client, "Some task").get_json()["id"]
    res = client.put(f"/api/tasks/{task_id}", json={"done": "yes"})
    assert res.status_code == 400


def test_update_with_invalid_priority_returns_400(client):
    task_id = add_task(client, "Some task").get_json()["id"]
    res = client.put(f"/api/tasks/{task_id}", json={"priority": "urgent"})
    assert res.status_code == 400



def test_delete_task_returns_200(client):
    task_id = add_task(client, "To be deleted").get_json()["id"]
    res = client.delete(f"/api/tasks/{task_id}")
    assert res.status_code == 200


def test_deleted_task_no_longer_in_list(client):
    task_id = add_task(client, "To be deleted").get_json()["id"]
    client.delete(f"/api/tasks/{task_id}")
    data = client.get("/api/tasks").get_json()
    ids = [t["id"] for t in data["tasks"]]
    assert task_id not in ids


def test_delete_nonexistent_task_returns_404(client):
    res = client.delete("/api/tasks/999")
    assert res.status_code == 404