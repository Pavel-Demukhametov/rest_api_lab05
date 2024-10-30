import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from config import ACCESS_TOKEN, API_URL
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

session = requests.Session()
adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100)
session.mount("https://", adapter)

@lru_cache(maxsize=1000)
def fetch_user_info(user_identifier, session=session):
    endpoint = f"{API_URL}users.get"
    parameters = {
        "user_ids": user_identifier,
        "fields": "screen_name,first_name,last_name,sex,home_town,city",
        "access_token": ACCESS_TOKEN,
        "v": "5.199",
        "lang": 0
    }
    try:
        response = session.get(endpoint, params=parameters, timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'error' in data:
            logger.error(f"Ошибка при получении информации о пользователе: {data['error']['error_msg']}")
            return None
        return data['response'][0]
    except requests.RequestException as e:
        logger.error(f"Исключение запроса: {e}")
        raise

def fetch_followers(user_id, session=session):
    all_followers = []
    count_per_request = 100
    offset = 0
    max_followers = 100

    while len(all_followers) < max_followers:
        endpoint = f"{API_URL}users.getFollowers"
        parameters = {
            "user_id": user_id,
            "count": count_per_request,
            "offset": offset,
            "access_token": ACCESS_TOKEN,
            "v": "5.199",
            "lang": 0
        }
        try:
            response = session.get(endpoint, params=parameters, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'error' in data:
                logger.error(f"Ошибка при получении подписчиков: {data['error']['error_msg']}")
                break

            followers = data['response']['items']
            all_followers.extend(followers)
            logger.debug(f"Получено {len(followers)} подписчиков на шаге с offset={offset}")

            if len(all_followers) >= max_followers:
                all_followers = all_followers[:max_followers]
                break

            if len(followers) < count_per_request:
                break

            offset += count_per_request

        except requests.RequestException as e:
            logger.error(f"Исключение запроса: {e}")
            break

    logger.info(f"Всего подписчиков для пользователя {user_id}: {len(all_followers)}")
    return all_followers

def fetch_subscriptions(user_id, session=session):
    all_users = []
    all_groups = []
    count_per_request = 100
    offset = 0
    max_subscriptions = 100

    while len(all_users) + len(all_groups) < max_subscriptions:
        endpoint = f"{API_URL}users.getSubscriptions"
        parameters = {
            "user_id": user_id,
            "extended": 1,
            "count": count_per_request,
            "offset": offset,
            "access_token": ACCESS_TOKEN,
            "v": "5.199",
            "lang": 0
        }

        try:
            response = session.get(endpoint, params=parameters, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'error' in data:
                logger.error(f"Ошибка при получении подписок: {data['error']['error_msg']}")
                break

            subscriptions = data['response']['items']
            users = [sub for sub in subscriptions if sub.get('type', '').lower() == 'profile']
            groups = [sub for sub in subscriptions if sub.get('type', '').lower() == 'group']

            all_users.extend(users)
            all_groups.extend(groups)
            logger.debug(f"Получено {len(users)} пользователей и {len(groups)} групп на шаге с offset={offset}")

            if len(all_users) + len(all_groups) >= max_subscriptions:
                all_users = all_users[:max_subscriptions]
                all_groups = all_groups[:max_subscriptions]
                break

            if len(subscriptions) < count_per_request:
                break

            offset += count_per_request

        except requests.RequestException as e:
            logger.error(f"Исключение запроса: {e}")
            break

    logger.info(f"Всего подписок для пользователя {user_id}: {len(all_users)} пользователей и {len(all_groups)} групп")
    return {'users': all_users, 'groups': all_groups}

def process_user(user_id, depth, processed_users, neo4j_handler, session=session):
    if depth > 2 or user_id in processed_users:
        return
    processed_users.add(user_id)
    logger.info(f"Обработка пользователя {user_id} на глубине {depth}")

    user_info = fetch_user_info(user_id, session)
    if not user_info:
        return

    neo4j_handler.create_user_node(user_info)

    followers = fetch_followers(user_id, session)
    subscriptions = fetch_subscriptions(user_id, session)

    # Обработка подписчиков
    for follower_id in followers:
        if follower_id not in processed_users:
            follower_info = fetch_user_info(follower_id, session)
            if follower_info:
                neo4j_handler.create_user_node(follower_info)
                neo4j_handler.create_follower_relationship(follower_id, user_id)
                if depth < 2:
                    process_user(follower_id, depth + 1, processed_users, neo4j_handler, session)

    # Обработка подписок на пользователей
    for sub_user in subscriptions['users']:
        sub_user_id = sub_user.get('id')
        if sub_user_id and sub_user_id not in processed_users:
            sub_user_info = fetch_user_info(sub_user_id, session)
            if sub_user_info:
                neo4j_handler.create_user_node(sub_user_info)
                neo4j_handler.create_subscribe_relationship(user_id, sub_user_id)
                if depth < 2:
                    process_user(sub_user_id, depth + 1, processed_users, neo4j_handler, session)

    # Обработка подписок на группы
    for group in subscriptions['groups']:
        group_id = group.get('id')
        if group_id:
            neo4j_handler.create_group_node(group)
            neo4j_handler.create_subscribe_relationship(user_id, -group_id)

    logger.info(f"Завершена обработка пользователя {user_id} на глубине {depth}")