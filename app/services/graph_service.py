from neo4j import GraphDatabase
import logging
from app.config import NEO4J_BOLT_URL, NEO4J_USERNAME, NEO4J_PASSWORD
from app.models.node_model import NodeCreate, Relationship
from typing import Dict, List

logger = logging.getLogger(__name__)

class Neo4jHandler:
    def __init__(self):
        self.driver = self._init_driver()

    def _init_driver(self):
        try:
            driver = GraphDatabase.driver(
                NEO4J_BOLT_URL,
                auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
            )
            logger.info("Соединение с Neo4j успешно установлено.")
            return driver
        except Exception as e:
            logger.error(f"Не удалось подключиться к Neo4j: {e}")
            return None

    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Соединение с Neo4j закрыто.")

    def get_all_nodes(self):
        query = "MATCH (n) RETURN n.id AS id, labels(n) AS label"
        with self.driver.session() as session:
            result = session.run(query)
            return [{"id": record["id"], "label": record["label"]} for record in result]

    def get_node_with_relationships(self, node_id: int):
        query = """
        MATCH (n {id: $id})-[r_out]->(m_out)
        RETURN n, labels(n) AS label, TYPE(r_out) AS relationship_type, m_out AS related_node, labels(m_out) AS related_label, 'outgoing' AS direction
        UNION ALL
        MATCH (n {id: $id})<-[r_in]- (m_in)
        RETURN n, labels(n) AS label, TYPE(r_in) AS relationship_type, m_in AS related_node, labels(m_in) AS related_label, 'incoming' AS direction
        """
        with self.driver.session() as session:
            result = session.run(query, {"id": node_id})
            nodes = []
            for record in result:
                relationship_type = record["relationship_type"] if record["relationship_type"] else None
                direction = record["direction"]

                if relationship_type is None:
                    continue

                related_node = record["related_node"]
                related_label = record["related_label"]
                
                if related_node:
                    related_node_data = {**dict(related_node), "label": related_label[0]}
                else:
                    related_node_data = None
                
                nodes.append({
                    "node": {**dict(record["n"]), "label": record["label"][0]},
                    "relationship": relationship_type,
                    "direction": direction,
                    "related_node": related_node_data
                })
            if not nodes:
                return []
            return nodes
    def create_node(self, data: NodeCreate):
        query = f"""
        MERGE (n:{data.label} {{id: $id}})
        SET n += $attributes
        """
        parameters = {"id": data.id, "attributes": data.attributes or {}}
        with self.driver.session() as session:
            session.run(query, parameters)

            if data.relationships:
                for rel in data.relationships:
                    rel_query = f"""
                    MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
                    MERGE (a)-[:{rel.type}]->(b)
                    """
                    session.run(rel_query, {"from_id": data.id, "to_id": rel.to_id})
        return {"message": f"Node with id {data.id} and relationships created successfully"}

    def delete_node(self, node_id: int):
        query = "MATCH (n {id: $id}) DETACH DELETE n"
        with self.driver.session() as session:
            result = session.run(query, {"id": node_id})
            summary = result.consume()
            return summary.counters.nodes_deleted > 0