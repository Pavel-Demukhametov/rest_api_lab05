# vk_api.py
# vk_api.py
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from config import ACCESS_TOKEN, API_URL
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Настраиваем глобальную сессию с увеличенным пулом соединений
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
    count_per_request = 10
    offset = 0
    max_followers = 10  # Максимальное количество подписчиков для запроса

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

            # Проверяем, достигли ли мы максимального количества подписчиков
            if len(all_followers) >= max_followers:
                all_followers = all_followers[:max_followers]  # Ограничиваем список до max_followers
                break

            # Если получено меньше, чем запрошено, то это последний запрос
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
    count_per_request = 200
    offset = 0

    while True:
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

            # Временное логирование для проверки структуры данных
            if offset == 0:
                logger.debug(f"Пример подписок: {subscriptions[:5]}")
                for sub in subscriptions[:5]:
                    logger.debug(f"Тип подписки: {sub.get('type')}")

            users = [sub for sub in subscriptions if sub.get('type', '').lower() == 'profile']
            groups = [sub for sub in subscriptions if sub.get('type', '').lower() == 'group']

            all_users.extend(users)
            all_groups.extend(groups)
            logger.debug(f"Получено {len(users)} пользователей и {len(groups)} групп на шаге с offset={offset}")

            if len(subscriptions) < count_per_request:
                break

            offset += count_per_request

        except requests.RequestException as e:
            logger.error(f"Исключение запроса: {e}")
            break

    logger.info(f"Всего подписок для пользователя {user_id}: {len(all_users)} пользователей и {len(all_groups)} групп")
    return {'users': all_users, 'groups': all_groups}

def process_user(user_id, depth, processed_users, neo4j_handler, session=session, max_workers=10):
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

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Обработка подписчиков параллельно
        follower_futures = {
            executor.submit(process_user, follower_id, depth + 1, processed_users, neo4j_handler, session, max_workers): follower_id
            for follower_id in followers
        }

        # Параллельное получение информации о подписанных пользователях
        user_subscription_futures = {
            executor.submit(fetch_user_info, sub_user['id'], session): sub_user['id']
            for sub_user in subscriptions['users'] if 'id' in sub_user
        }

        # Асинхронная обработка результатов подписчиков
        for future in as_completed(follower_futures):
            follower_id = follower_futures[future]
            try:
                future.result()
            except Exception as e:
                logger.error(f"Ошибка при обработке подписчика {follower_id}: {e}")

        # Асинхронная обработка результатов подписок
        for future in as_completed(user_subscription_futures):
            sub_user_id = user_subscription_futures[future]
            try:
                sub_user_info = future.result()
                if sub_user_info:
                    neo4j_handler.create_user_node(sub_user_info)
                    neo4j_handler.create_subscribe_relationship(user_id, sub_user_id)
                    if depth < 2:
                        process_user(sub_user_info['id'], depth + 1, processed_users, neo4j_handler, session, max_workers)
            except Exception as e:
                logger.error(f"Ошибка при обработке подписки пользователя {sub_user_id}: {e}")

        # Обработка групп
        for group in subscriptions['groups']:
            if 'id' in group:
                neo4j_handler.create_group_node(group)
                neo4j_handler.create_subscribe_relationship(user_id, -group['id'])

    logger.info(f"Завершена обработка пользователя {user_id} на глубине {depth}")