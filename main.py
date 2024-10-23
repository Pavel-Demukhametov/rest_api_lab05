import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("VK_TOKEN")
API_URL = "https://api.vk.com/method/"
def fetch_user_info(user_identifier):
    endpoint = f"{API_URL}users.get"
    parameters = {
        "user_ids": user_identifier,
        "fields": "followers_count",
        "access_token": ACCESS_TOKEN,
        "v": "5.131"
    }
    response = requests.get(endpoint, params=parameters)
    return response.json()

def fetch_followers(user_identifier):
    endpoint = f"{API_URL}users.getFollowers"
    parameters = {
        "user_id": user_identifier,
        "access_token": ACCESS_TOKEN,
        "v": "5.131"
    }
    response = requests.get(endpoint, params=parameters)
    return response.json()

def fetch_follower_details(follower_ids):
    endpoint = f"{API_URL}users.get"
    parameters = {
        "user_ids": ",".join(map(str, follower_ids)),
        "fields": "first_name,last_name",
        "access_token": ACCESS_TOKEN,
        "v": "5.131"
    }
    response = requests.get(endpoint, params=parameters)
    return response.json()

def fetch_subscriptions(user_identifier):
    endpoint = f"{API_URL}users.getSubscriptions"
    parameters = {
        "user_id": user_identifier,
        "access_token": ACCESS_TOKEN,
        "v": "5.131"
    }
    response = requests.get(endpoint, params=parameters)
    return response.json()

def fetch_group_details(group_ids):
    endpoint = f"{API_URL}groups.getById"
    parameters = {
        "group_ids": ",".join(map(str, group_ids)),
        "fields": "name",
        "access_token": ACCESS_TOKEN,
        "v": "5.131"
    }
    response = requests.get(endpoint, params=parameters)
    return response.json()

def write_to_json_file(data, output_filename="vk_user_data.json"):
    output_path = os.path.join(os.getcwd(), output_filename)
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    print(f"Данные успешно сохранены в файл {output_path}")


if not ACCESS_TOKEN:
    print("Ошибка: Токен VK не установлен в переменных окружения.")
else:
    user_input = input("Введите ID пользователя или его screen_name: ")
    if user_input == "":
        print("Не было переданно значение. Используется https://vk.com/dm")
        user_input = "dm"
        
    user_info = fetch_user_info(user_input)

    if user_info and 'response' in user_info:
        user_details = user_info['response'][0]
        user_id = user_details['id']

        if user_details.get('is_closed', True):
            followers_info, subscriptions_info = {}, {}
        else:
            followers_info = fetch_followers(user_id)
            if 'response' in followers_info:
                follower_ids = followers_info['response']['items']
                follower_details = fetch_follower_details(follower_ids)
                followers_info['details'] = follower_details['response']

            subscriptions_info = fetch_subscriptions(user_id)
            if 'response' in subscriptions_info and 'groups' in subscriptions_info['response']:
                group_ids = subscriptions_info['response']['groups']['items']
                group_details = fetch_group_details(group_ids)
                subscriptions_info['details'] = group_details['response']

        result_data = {
            "user": user_info,
            "followers": followers_info,
            "subscriptions": subscriptions_info
        }
        write_to_json_file(result_data)
    else:
        print("Не удалось получить данные о пользователе.")
