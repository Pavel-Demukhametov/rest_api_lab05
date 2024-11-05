# Lab 05 RestAPI

## Оглавление
1. [Описание](#описание)
2. [Стек технологий](#стек-технологий)
3. [Функциональные возможности](#функциональные-возможности)
4. [Структура данных](#структура-данных)
5. [API и тестирование](#api-и-тестирование)
6. [Установка и запуск](#установка-и-запуск)
7. [Полезные ссылки](#полезные-ссылки)
8. [Maintainers](#maintainers)

## Описание

Приложение написано на Python с использованием FastAPI. Оно подключается к базе данных Neo4j для хранения и обработки данных о пользователях и группах, а также их связях. Приложение имеет эндпоинты для работы с данными, обеспечивая добавление, удаление и получение информации об узлах и связях

- **Работа с узлами и связями**: Приложение поддерживает операции создания узлов, добавления связей между ними, а также удаления узлов со всеми их связями.
- **Авторизация через токен**: Для доступа к точкам с изменением данных реализована авторизация через JWT токен.

## Стек технологий
- Python
- FastAPI
- Neo4j
- Pytest
- JWT для аутентификации

## Функциональные возможности
- Создание узлов и связей между ними.
- Получение данных о всех об узлах и их связях.
- Получение данных о конретном узле.
- Удаление узлов вместе с их связями.

## Структура данных
### Узлы
- **User**: Данные о пользователе
  - `id`: Уникальный идентификатор пользователя
  - `screen_name`: Имя пользователя
  - `name`: Полное имя пользователя
  - `sex`: Пол
  - `home_town`: Город или местоположение

- **Group**: Данные о группах
  - `id`: Уникальный идентификатор группы
  - `name`: Название группы
  - `screen_name`: Имя группы

### Связи
- **Follow**: Подписчик на пользователя
- **Subscribe**: Подписка пользователя на группу

## API и тестирование
#### API Эндпоинты

1. **`POST /token`** - Получение токена авторизации

   - **Описание**: Позволяет авторизоваться пользователю и получить JWT токен для аутентификации.
   - **Тело запроса**:
     - `username` (string): Имя пользователя.
     - `password` (string): Пароль пользователя.
   - **Пример запроса**:
     ```json
     {
       "username": "admin",
       "password": "secret"
     }
     ```
   - **Пример ответа**:
     ```json
     {
       "access_token": "eyJhbGciOiJIUzI1NiIsInR5...",
       "token_type": "bearer"
     }
     ```

2. **`GET /nodes`** - Получение всех узлов

   - **Описание**: Возвращает список всех узлов в графе с их атрибутами.
   - **Параметры**: Отсутствуют.
   - **Пример запроса**:
     ```http
     GET /nodes
     ```
   - **Пример ответа**:
     ```json
     [
       {"id": 1001, "label": ["User"]},
       {"id": 1002, "label": ["User"]},
       {"id": 1003, "label": ["Group"]}
     ]
     ```
    - **Описание полей ответа**:
       - `id` (int): Идентификатор узла.
       - `label` (string): Метка узла (например, "User" или "Group").

3. **`GET /node/{node_id}`** - Получение узла и всех его связей

   - **Описание**: Возвращает информацию о конкретном узле, включая все доступные атрибуты узла, его исходящие и входящие связи, а также все доступные атрибуты связанных узлов.
   - **Параметры**:
     - `node_id` (int): Идентификатор узла, для которого необходимо получить информацию.
   - **Пример запроса**:
     ```http
     GET /node/288555774
     ```
   - **Пример ответа**:
     ```json
     [
       {
         "node": {
           "home_town": "",
           "screen_name": "puritanin9",
           "sex": 2,
           "name": "Павел Демухаметов",
           "id": 288555774,
           "label": "User"
         },
         "relationship": "Subscribe",
         "direction": "outgoing",
         "related_node": {
           "home_town": "Уфа",
           "screen_name": "blacksilverufa",
           "sex": 2,
           "name": "Артур Blacksilver",
           "id": 140277504,
           "label": "User"
         }
       },
       {
         "node": {
           "home_town": "",
           "screen_name": "puritanin9",
           "sex": 2,
           "name": "Павел Демухаметов",
           "id": 288555774,
           "label": "User"
         },
         "relationship": "Follow",
         "direction": "incoming",
         "related_node": {
           "home_town": "Москва",
           "screen_name": "abakhrakh",
           "sex": 2,
           "name": "Андрей Бахрах",
           "id": 155498565,
           "label": "User"
         }
       }
     ]
     ```
   - **Описание полей ответа**:
     - **`node`**: Информация о запрашиваемом узле, со всеми доступными атрибутами.
       - `home_town` (string): Родной город узла.
       - `screen_name` (string): Имя пользователя.
       - `sex` (int): Пол пользователя.
       - `name` (string): Имя пользователя.
       - `id` (int): Идентификатор узла.
       - `label` (string): Метка узла (например, "User" или "Group").
     - **`relationship`**: Тип связи между узлом и `related_node`, `Subscribe` или `Follow`.
     - **`direction`**: Направление связи относительно `node`:
       - `outgoing`: Исходящая связь (узел подписан на `related_node`).
       - `incoming`: Входящая связь (на узел подписан `related_node`).
     - **`related_node`**: Описание узла, связанного с `node`, со всеми доступными атрибутами, аналогично `node`.

4. **`POST /node`** - Создание узла и его связей

   - **Описание**: Создает новый узел и добавляет связи с другими узлами, если указаны.
   - **Требуется токен аутентификации**.
   - **Тело запроса**:
     - `id` (int): Идентификатор узла.
     - `label` (string): Метка узла.
     - `attributes` (object, optional): Атрибуты узла.
     - `relationships` (list, optional): Связи узла с другими узлами.
   - **Пример запроса**:
     ```json
     {
       "id": 1004,
       "label": "User",
       "attributes": {"name": "Test User 4", "screen_name": "testuser4"},
       "relationships": [{"to_id": 1003, "type": "Subscribe"}]
     }
     ```
   - **Пример ответа**:
     - Статус: `204 No Content`

5. **`DELETE /node/{node_id}`** - Удаление узла и его связей

   - **Описание**: Удаляет узел по идентификатору вместе с его связями.
   - **Требуется токен аутентификации**.
   - **Параметры**:
     - `node_id` (int): Идентификатор узла.
   - **Пример запроса**:
     ```http
     DELETE /node/1004
     ```
   - **Пример ответа**:
     - Статус: `204 No Content`

#### Описание тестов

1. **`test_get_node_with_relationships`** - Проверка получения узла и его связей

   - **Описание**: Проверяет, что данные узла и его связи возвращаются корректно для различных `node_id`.
   - **Параметры теста**:
     - `node_id`: ID узла, для которого выполняется запрос.
     - `expected_relationships`: Ожидаемые связи узла.
   - **Процедура теста**:
     - Выполняется запрос `GET /node/{node_id}`.
     - Проверяется, что статус ответа `200`.
     - Сравниваются данные узла и его связи с ожидаемыми значениями.

2. **`test_get_all_nodes`** - Проверка получения всех узлов

   - **Описание**: Проверяет, что все узлы в базе данных возвращаются как список.
   - **Процедура теста**:
     - Выполняется запрос `GET /nodes`.
     - Проверяется, что статус ответа `200`.
     - Убеждается, что ответ является списком.

3. **`test_delete_node`** - Проверка удаления узла и его связей

   - **Описание**: Проверяет, что узел с конкретным `node_id` и его связи корректно удаляются.
   - **Параметры теста**:
     - `node_id`: ID удаляемого узла.
   - **Процедура теста**:
     - Выполняется запрос `DELETE /node/{node_id}` с токеном аутентификации.
     - Проверяется, что статус ответа `204`.
     - Подтверждается, что узел больше не существует, отправляя запрос `GET` и проверяя статус `404`.

4. **`test_create_node_unauthorized`** - Проверка создания узла без авторизации

   - **Описание**: Проверяет, что попытка создания узла с невалидным токеном возвращает `401 Unauthorized`.
   - **Процедура теста**:
     - Выполняется запрос `POST /node` с неверным токеном.
     - Ожидается ответ `401 Unauthorized`.

5. **`test_delete_node_unauthorized`** - Проверка удаления узла без авторизации

   - **Описание**: Проверяет, что попытка удаления узла с невалидным токеном возвращает `401 Unauthorized`.
   - **Процедура теста**:
     - Выполняется запрос `DELETE /node/{node_id}` с неверным токеном.
     - Ожидается ответ `401 Unauthorized`.


## Установка и запуск

1. Клонирование репозитория
`git clone https://github.com/Pavel-Demukhametov/nosql_lab04.git`

2. Переход в папку с репозиторием
`cd <название папки в которую клонировали репозиторий>`

3. Чтобы восстановить базу данных, перейдите в каталог, где находится утилита `neo4j-admin` (например, `D:\neo4j\relate-data\dbmss\<ваш dbms идентификатор>\bin`), и выполните следующую команду:

```bash
neo4j-admin database load neo4j --from-path="путь до вашего dump файла" --overwrite-destination=true
```

4. Создание виртуального окружения
Windows
`python -m venv venv`
Linux 
`python3 -m venv venv`

5. Активация виртуального окружения
Windows
`.\venv\Scripts\activate`
Linux
`source venv/bin/activate`

6. Установка зависимостей.
`pip install -r requirements.txt`

7. Установка переменных окружения
   **Подключение к базе данных Neo4j:**
   - `NEO4J_BOLT_URL` — URL для подключения к Neo4j через протокол Bolt. По умолчанию: `bolt://localhost:7687`.
   - `NEO4J_USERNAME` — имя пользователя для подключения к базе данных Neo4j. По умолчанию: `neo4j`.
   - `NEO4J_PASSWORD` — пароль для подключения к базе данных Neo4j. По умолчанию: `12345678`.
   
   Пример:
   ```
        NEO4J_BOLT_URL = <Ваш URL>
        NEO4J_USERNAME = <Ваше имя пользователя>
        NEO4J_PASSWORD = <Ваш пароль>
    ```
 

8. **Запуск приложения**:
   Для запуска приложения используйте следующую команду:

   `uvicorn app.main:app --host 0.0.0.0 --port 8000`

   Приложение будет доступно по адресу `http://localhost:8000`.

9. **Запуск тестов**:
   Чтобы запустить тесты, выполните команду:

   `pytest`

## Полезные ссылки

- [Документация FastAPI](https://fastapi.tiangolo.com/)
- [Neo4j](https://neo4j.com)

## Maintainers

- Developed by [Pavel Demukhametov](https://github.com/Pavel-Demukhametov)