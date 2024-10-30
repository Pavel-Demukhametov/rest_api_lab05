from neo4j import GraphDatabase
import logging
from config import NEO4J_BOLT_URL, NEO4J_USERNAME, NEO4J_PASSWORD

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

    def create_user_node(self, user_data: dict):
        query = """
            MERGE (u:User {id: $id})
            SET u.screen_name = $screen_name,
                u.name = $name,
                u.sex = $sex,
                u.home_town = $home_town
        """
        parameters = {
            'id': user_data['id'],
            'screen_name': user_data.get('screen_name', ''),
            'name': f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}",
            'sex': user_data.get('sex', 0),
            'home_town': user_data.get('home_town', user_data.get('city', {}).get('title', ''))
        }
        with self.driver.session() as session:
            session.run(query, parameters)
        logger.debug(f"Создан или обновлён узел пользователя {user_data['id']}")

    def create_group_node(self, group_data: dict):
        query = """
            MERGE (g:Group {id: $id})
            SET g.name = $name,
                g.screen_name = $screen_name
        """
        parameters = {
            'id': -group_data['id'],  # Отрицательный ID для групп
            'name': group_data.get('name', ''),
            'screen_name': group_data.get('screen_name', '')
        }
        with self.driver.session() as session:
            session.run(query, parameters)
        logger.debug(f"Создан или обновлён узел группы {group_data['id']}")
        
    def create_follower_relationship(self, follower_id: int, user_id: int):
        query = """
            MATCH (f:User {id: $follower_id})
            MATCH (u:User {id: $user_id})
            MERGE (f)-[:Follow]->(u)
        """
        parameters = {'follower_id': follower_id, 'user_id': user_id}
        with self.driver.session() as session:
            session.run(query, parameters)
        logger.debug(f"Добавлена связь Follow между {follower_id} и {user_id}")



    def create_subscribe_relationship(self, from_id: int, to_id: int):
        query = """
            MATCH (a:User {id: $from_id})
            MATCH (b {id: $to_id})
            MERGE (a)-[:Subscribe]->(b)
        """
        parameters = {'from_id': from_id, 'to_id': to_id}
        with self.driver.session() as session:
            session.run(query, parameters)
        logger.debug(f"Добавлена связь Subscribe между {from_id} и {to_id}")

    def execute_queries(self, args):
        with self.driver.session() as session:
            if args.total_users:
                result = session.run("MATCH (u:User) RETURN COUNT(u) AS total_users")
                total_users = result.single()['total_users']
                print(f"Всего пользователей: {total_users}")

            if args.total_groups:
                result = session.run("MATCH (g:Group) RETURN COUNT(g) AS total_groups")
                total_groups = result.single()['total_groups']
                print(f"Всего групп: {total_groups}")

            if args.top_users:
                query = """
                    MATCH (u:User)<-[:Follow]-(f:User)
                    RETURN u.id AS user_id, u.name AS name, COUNT(f) AS followers
                    ORDER BY followers DESC
                    LIMIT 5
                """
                result = session.run(query)
                print("Топ 5 пользователей по количеству подписчиков:")
                for record in result:
                    print(f"{record['name']} (ID: {record['user_id']}) - {record['followers']} подписчиков")

            if args.top_groups:
                query = """
                    MATCH (g:Group)<-[:Subscribe]-(u:User)
                    RETURN g.id AS group_id, g.name AS name, COUNT(u) AS subscribers
                    ORDER BY subscribers DESC
                    LIMIT 5
                """
                result = session.run(query)
                print("Топ 5 групп по количеству подписчиков:")
                for record in result:
                    print(f"{record['name']} (ID: {record['group_id']}) - {record['subscribers']} подписчиков")

            if args.mutual_followers:
                query = """
                    MATCH (u1:User)-[:Follow]->(u2:User),
                          (u2)-[:Follow]->(u1)
                    WHERE u1.id < u2.id
                    RETURN u1.name AS user1, u2.name AS user2
                """
                result = session.run(query)
                print("Пользователи, которые подписаны друг на друга:")
                mutual_followers_found = False
                for record in result:
                    print(f"{record['user1']} и {record['user2']}")
                    mutual_followers_found = True
                if not mutual_followers_found:
                    print("Нет пользователей, которые подписаны друг на друга.")