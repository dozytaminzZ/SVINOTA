import allure


@allure.epic("Лобби")
@allure.feature("Создание комнаты")
class TestCreateRoom:

    @allure.story("Успешное создание")
    @allure.title("Авторизованный пользователь создаёт публичную комнату с дефолтными параметрами")
    def test_create_room_defaults(self, owner_client):
        client, owner_id = owner_client

        with allure.step("Отправляем POST /lobby/create без тела"):
            response = client.post("/lobby/create", json={})

        with allure.step("Проверяем, что комната создана"):
            assert response.status_code == 201
            data = response.get_json()
            assert data["status"] == "ok"
            room = data["room"]
            assert room["owner_id"] == owner_id
            assert room["status"] == "waiting"
            assert room["max_players"] == 6
            assert room["is_private"] is False
            assert room["players_count"] == 1
            assert room["ready_count"] == 0
            assert len(room["invite_code"]) == 8

    @allure.story("Успешное создание")
    @allure.title("Создание приватной комнаты на 4 игрока")
    def test_create_private_room(self, owner_client):
        client, _ = owner_client

        with allure.step("Создаём приватную комнату на 4 игрока"):
            response = client.post("/lobby/create", json={
                "max_players": 4,
                "is_private": True,
            })

        with allure.step("Проверяем параметры комнаты"):
            assert response.status_code == 201
            room = response.get_json()["room"]
            assert room["max_players"] == 4
            assert room["is_private"] is True

    @allure.story("Валидация параметров")
    @allure.title("Нечисловой max_players возвращает 400")
    def test_create_room_invalid_max_players_type(self, owner_client):
        client, _ = owner_client

        with allure.step("Отправляем строку вместо числа"):
            response = client.post("/lobby/create", json={"max_players": "abc"})

        with allure.step("Проверяем ошибку"):
            assert response.status_code == 400
            assert response.get_json()["error"] == "max_players must be an integer"

    @allure.story("Валидация параметров")
    @allure.title("max_players меньше 2 отклоняется")
    def test_create_room_max_players_too_small(self, owner_client):
        client, _ = owner_client

        with allure.step("Отправляем max_players=1"):
            response = client.post("/lobby/create", json={"max_players": 1})

        with allure.step("Проверяем ошибку"):
            assert response.status_code == 400
            assert response.get_json()["error"] == "max_players must be between 2 and 6"

    @allure.story("Валидация параметров")
    @allure.title("max_players больше 6 отклоняется")
    def test_create_room_max_players_too_big(self, owner_client):
        client, _ = owner_client

        with allure.step("Отправляем max_players=7"):
            response = client.post("/lobby/create", json={"max_players": 7})

        with allure.step("Проверяем ошибку"):
            assert response.status_code == 400
            assert response.get_json()["error"] == "max_players must be between 2 and 6"

    @allure.story("Авторизация")
    @allure.title("Неавторизованный пользователь не может создать комнату")
    def test_create_room_requires_auth(self, client):
        with allure.step("Отправляем запрос без авторизации"):
            response = client.post("/lobby/create", json={})

        with allure.step("Проверяем, что доступ запрещён"):
            assert response.status_code == 401

    @allure.story("Один пользователь — одна комната")
    @allure.title("Пользователь, уже состоящий в комнате, не может создать новую")
    def test_create_room_when_already_in_room(self, owner_client):
        client, _ = owner_client

        with allure.step("Создаём первую комнату"):
            first = client.post("/lobby/create", json={})
            assert first.status_code == 201

        with allure.step("Пробуем создать вторую"):
            second = client.post("/lobby/create", json={})

        with allure.step("Проверяем, что вторая отклонена"):
            assert second.status_code == 409
            assert second.get_json()["error"] == "user already in a room"

    @allure.story("Уникальность invite_code")
    @allure.title("Каждая новая комната получает уникальный invite_code")
    def test_invite_codes_are_unique(self, owner_client, guest_client, third_client):
        codes = set()
        for client, _ in (owner_client, guest_client, third_client):
            response = client.post("/lobby/create", json={})
            assert response.status_code == 201
            codes.add(response.get_json()["room"]["invite_code"])

        with allure.step("Проверяем уникальность кодов"):
            assert len(codes) == 3
