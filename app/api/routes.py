from fastapi import APIRouter, HTTPException, Depends
from app.services.graph_service import Neo4jHandler
from app.models.node_model import NodeCreate
from typing import List, Dict, Optional
from app.utils.security import get_current_user  # Импортируем зависимость для авторизации

router = APIRouter()
neo4j_handler = Neo4jHandler()

@router.get("/nodes")
def get_all_nodes():
    """Получить все узлы с атрибутами id и label."""
    nodes = neo4j_handler.get_all_nodes()
    return nodes

@router.get("/node/{node_id}")
def get_node_with_relationships(node_id: int):
    """Получить узел и все его связи со всеми атрибутами."""
    node = neo4j_handler.get_node_with_relationships(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node

@router.post("/node", dependencies=[Depends(get_current_user)])
def create_node(data: NodeCreate):
    """Создать узел и его связи."""
    result = neo4j_handler.create_node(data)
    return result

@router.delete("/node/{node_id}", dependencies=[Depends(get_current_user)])
def delete_node(node_id: int):
    """Удалить узел и все его связи."""
    result = neo4j_handler.delete_node(node_id)
    if not result:
        raise HTTPException(status_code=404, detail="Node not found or already deleted")
    return {"message": "Node and its relationships deleted successfully"}