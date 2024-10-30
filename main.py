# main.py
import logging
import argparse
from vk_api import fetch_user_info, process_user, session
from neo4j_db import Neo4jHandler
from logger import setup_logging
from config import ACCESS_TOKEN

def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    if not ACCESS_TOKEN:
        logger.error("VK API токен не найден в переменных окружения.")
        return

    user_input = input("Введите ID пользователя или его screen_name: ")
    if not user_input:
        logger.info("Не было передано значение. Используется https://vk.com/dm")
        user_input = "dm"

    user_info = fetch_user_info(user_input, session)
    if not user_info:
        logger.error("Не удалось получить информацию о пользователе.")
        return

    neo4j_handler = Neo4jHandler()
    if neo4j_handler.driver is None:
        logger.error("Не удалось подключиться к Neo4j. Программа завершена.")
        return

    try:
        process_user(user_info['id'], depth=0, processed_users=set(), neo4j_handler=neo4j_handler, session=session)
        logger.info("Сбор и сохранение данных завершены.")

        parser = argparse.ArgumentParser(description='VK Data Analyzer')
        parser.add_argument('--total_users', action='store_true', help='Всего пользователей')
        parser.add_argument('--total_groups', action='store_true', help='Всего групп')
        parser.add_argument('--top_users', action='store_true', help='Топ 5 пользователей по количеству подписчиков')
        parser.add_argument('--top_groups', action='store_true', help='Топ 5 групп по количеству подписчиков')
        parser.add_argument('--mutual_followers', action='store_true', help='Пользователи, которые подписаны друг на друга')

        args = parser.parse_args()
        neo4j_handler.execute_queries(args)

    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")

    finally:
        neo4j_handler.close()
        logger.info("Соединение с Neo4j закрыто.")

if __name__ == "__main__":
    main()