import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_BOLT_URL = os.getenv("NEO4J_BOLT_URL", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")

driver = None

def setup_database():
    global driver
    if driver is None:
        driver = GraphDatabase.driver(
            NEO4J_BOLT_URL,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )

def close_database():
    global driver
    if driver:
        driver.close()
        driver = None