import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import setup_database, close_database

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    """
    Настройка и очистка базы данных перед и после выполнения тестов.
    """
    setup_database()
    yield
    close_database()

@pytest.fixture(scope="module")
def auth_token():
    """
    Получение JWT токена для аутентифицированных запросов.
    """
    response = client.post(
        "/token",
        data={"username": "admin", "password": "secret1234"},  # неверный пароль для теста
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 200, f"Failed to obtain token: {response.status_code}"
    
    data = response.json()
    return data["access_token"]

node_data_table = [
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
    {
        "id": 1003,
        "label": "Group",
        "attributes": {"name": "Test Group", "screen_name": "testgroup"},
        "relationships": []
    },
]


@pytest.mark.parametrize("node_data", node_data_table)
def test_create_nodes(node_data, auth_token):
    """
    Тестирование создания узлов с заданными отношениями.
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.post("/node", json=node_data, headers=headers)
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    data = response.json()
    expected_message = f"Node with id {node_data['id']} and relationships created successfully"
    assert data["message"] == expected_message, f"Expected message '{expected_message}', got '{data['message']}'"
@pytest.mark.parametrize("node_id, expected_relationships", [
    (
        1001, 
        [
            {"to_id": 1003, "type": "Subscribe"},
            {"from_id": 1002, "type": "Follow"}
        ]
    ),
    (
        1002, 
        [
            {"to_id": 1001, "type": "Follow"} 
        ]
    ),
    (
        1003, 
        [
            {"from_id": 1001, "type": "Subscribe"}
        ]
    ),
])
def test_get_node_with_relationships(node_id, expected_relationships):
    """
    Тестирование получения узлов с их связями.
    Проверяет как входящие, так и исходящие связи.
    """
    response = client.get(f"/node/{node_id}")
    assert response.status_code == 200, f"Unexpected status code for node {node_id}: {response.status_code}"
    data = response.json()

    assert isinstance(data, list), f"Data type is not list: {data}"

    expected_rels = expected_relationships.copy()

    for rel in data:
        related_node = rel.get("related_node")
        if related_node is None:
            pytest.fail(f"Unexpected relationship: {{'relationship': {rel.get('relationship')}, 'direction': {rel.get('direction')}}}")
        
        related_node_id = related_node["id"]
        relationship_type = rel["relationship"]
        direction = rel["direction"]

        if direction == "outgoing":
            expected = {"to_id": related_node_id, "type": relationship_type}
        elif direction == "incoming":
            expected = {"from_id": related_node_id, "type": relationship_type}
        else:
            pytest.fail(f"Unknown relationship direction: {direction}")

        if expected in expected_rels:
            expected_rels.remove(expected)
        else:
            pytest.fail(f"Unexpected relationship: {expected}")

    assert not expected_rels, f"Missing expected relationships: {expected_rels}"

def test_get_all_nodes():
    """
    Тестирование получения всех узлов.
    """
    response = client.get("/nodes")
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    data = response.json()
    assert isinstance(data, list), f"Expected a list, but got {type(data)}"

# @pytest.mark.parametrize("node_id", [1001, 1002, 1003])
# def test_delete_node(node_id, auth_token):
#     """
#     Тестирование удаления узлов и их связей.
#     """
#     headers = {"Authorization": f"Bearer {auth_token}"}
#     response = client.delete(f"/node/{node_id}", headers=headers)
#     assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
#     data = response.json()
#     assert data["message"] == "Node and its relationships deleted successfully", f"Unexpected message: {data['message']}"
    
#     response = client.get(f"/node/{node_id}")
#     assert response.status_code == 404, f"Node {node_id} was not deleted as expected"