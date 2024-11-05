from fastapi import APIRouter, HTTPException, Depends, status
from app.services.graph_service import Neo4jHandler
from app.models.node_model import NodeCreate
from typing import List, Dict, Optional
from app.utils.security import get_current_user

router = APIRouter()
neo4j_handler = Neo4jHandler()

@router.get("/nodes")
def get_all_nodes():
    nodes = neo4j_handler.get_all_nodes()
    return nodes

@router.get("/node/{node_id}")
def get_node_with_relationships(node_id: int):
    node = neo4j_handler.get_node_with_relationships(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node

@router.post("/node", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user)])
def create_node(data: NodeCreate):
    neo4j_handler.create_node(data)
    return
    
@router.delete("/node/{node_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user)])
def delete_node(node_id: int):
    result = neo4j_handler.delete_node(node_id)
    if not result:
        raise HTTPException(status_code=404, detail="Node not found or already deleted")
    return