import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import setup_database, close_database
import time
import logging

client = TestClient(app)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    setup_database()
    yield
    close_database()

@pytest.fixture(scope="module")
def auth_token():
    response = client.post(
        "/token",
        data={"username": "admin", "password": "secret"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200, f"Failed to obtain token: {response.status_code}"
    return response.json()["access_token"]

node_data_table = [
    {
        "id": 1003,
        "label": "Group",
        "attributes": {"name": "Test Group", "screen_name": "testgroup"},
        "relationships": []
    },
    {
        "id": 1001,
        "label": "User",
        "attributes": {"name": "Test User 1", "screen_name": "testuser1"},
        "relationships": [{"to_id": 1003, "type": "Subscribe"}]
    },
    {
        "id": 1002,
        "label": "User",
        "attributes": {"name": "Test User 2", "screen_name": "testuser2"},
        "relationships": [{"to_id": 1001, "type": "Follow"}]
    },
]

@pytest.fixture(scope="module")
def create_nodes(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    for node_data in node_data_table:
        response = client.post("/node", json=node_data, headers=headers)
        logger.debug(f"Создание узла {node_data['id']}: статус {response.status_code}")
        assert response.status_code == 200, f"Failed to create node {node_data['id']}: {response.status_code}"
    # Проверка создания узлов
    for node_data in node_data_table:
        node_id = node_data["id"]
        assert wait_for_node(node_id), f"Node {node_id} not available in database after creation"
    yield
    # Опционально: удалить узлы после выполнения тестов

def wait_for_node(node_id, timeout=30):  # Увеличен таймаут до 30 секунд
    """Wait until node with `node_id` is available in database."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = client.get(f"/node/{node_id}")
        if response.status_code == 200:
            return True
        time.sleep(0.5)
    return False

@pytest.mark.usefixtures("create_nodes")
@pytest.mark.parametrize("node_id, expected_relationships", [
    (1001, [{"to_id": 1003, "type": "Subscribe"}, {"from_id": 1002, "type": "Follow"}]),
    (1002, [{"to_id": 1001, "type": "Follow"}]),
    (1003, [{"from_id": 1001, "type": "Subscribe"}]),
])
def test_get_node_with_relationships(node_id, expected_relationships):
    response = client.get(f"/node/{node_id}")
    assert response.status_code == 200, f"Unexpected status code for node {node_id}: {response.status_code}"
    data = response.json()
    expected_rels = expected_relationships.copy()

    for rel in data:
        related_node = rel.get("related_node")
        related_node_id = related_node["id"] if related_node else None
        relationship_type = rel["relationship"]
        direction = rel["direction"]

        expected = {"to_id": related_node_id, "type": relationship_type} if direction == "outgoing" else {"from_id": related_node_id, "type": relationship_type}
        assert expected in expected_rels, f"Unexpected relationship: {expected}"
        expected_rels.remove(expected)

    assert not expected_rels, f"Missing expected relationships: {expected_rels}"

@pytest.mark.usefixtures("create_nodes")
def test_get_all_nodes():
    response = client.get("/nodes")
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    assert isinstance(response.json(), list), "Response is not a list"

@pytest.mark.usefixtures("create_nodes")
@pytest.mark.parametrize("node_id", [1001, 1002, 1003])
def test_delete_node(node_id, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.delete(f"/node/{node_id}", headers=headers)
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    data = response.json()
    assert data["message"] == "Node and its relationships deleted successfully", f"Unexpected message: {data['message']}"

    response = client.get(f"/node/{node_id}")
    assert response.status_code == 404, f"Node {node_id} was not deleted as expected"