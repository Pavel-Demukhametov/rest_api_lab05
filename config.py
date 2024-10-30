import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("VK_TOKEN")
API_URL = "https://api.vk.com/method/"

NEO4J_BOLT_URL = os.getenv("NEO4J_BOLT_URL", "bolt://44.203.9.135:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "forty-heats-verification")