import allure


def _create_room(client, **kwargs):
    response = client.post("/lobby/create", json=kwargs)
    assert response.status_code == 201, response.get_json()
    return response.get_json()["room"]


@allure.epic("Лобби")
@allure.feature("Присоединение к комнате")
class TestJoinRoom:

    @allure.story("Успешное присоединение")
    @allure.title("Второй игрок входит в публичную комнату по room_id")
    def test_join_public_room_by_id(self, owner_client, guest_client):
        owner, _ = owner_client
        guest, guest_id = guest_client

        with allure.step("Владелец создаёт публичную комнату"):
            room = _create_room(owner)

        with allure.step("Второй игрок входит по room_id"):
            response = guest.post("/lobby/join", json={"room_id": room["id"]})

        with allure.step("Проверяем, что вход прошёл и счётчик игроков вырос"):
            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "ok"
            assert data["room"]["id"] == room["id"]
            assert data["room"]["players_count"] == 2

    @allure.story("Успешное присоединение")
    @allure.title("Вход в публичную комнату по invite_code")
    def test_join_public_room_by_invite_code(self, owner_client, guest_client):
        owner, _ = owner_client
        guest, _ = guest_client

        with allure.step("Владелец создаёт комнату"):
            room = _create_room(owner)

        with allure.step("Второй игрок входит по invite_code (в нижнем регистре — должен нормализоваться)"):
            response = guest.post("/lobby/join", json={"invite_code": room["invite_code"].lower()})

        with allure.step("Проверяем, что вход прошёл"):
            assert response.status_code == 200
            assert response.get_json()["room"]["players_count"] == 2

    @allure.story("Приватные комнаты")
    @allure.title("Войти в приватную комнату без invite_code нельзя")
    def test_join_private_room_without_invite_code(self, owner_client, guest_client):
        owner, _ = owner_client
        guest, _ = guest_client

        with allure.step("Владелец создаёт приватную комнату"):
            room = _create_room(owner, is_private=True)

        with allure.step("Второй игрок пробует войти только по room_id"):
            response = guest.post("/lobby/join", json={"room_id": room["id"]})

        with allure.step("Проверяем ошибку 403"):
            assert response.status_code == 403
            assert response.get_json()["error"] == "invite_code required for private room"

    @allure.story("Приватные комнаты")
    @allure.title("С правильным invite_code приватная комната пускает")
    def test_join_private_room_with_invite_code(self, owner_client, guest_client):
        owner, _ = owner_client
        guest, _ = guest_client

        with allure.step("Владелец создаёт приватную комнату"):
            room = _create_room(owner, is_private=True)

        with allure.step("Второй игрок входит по invite_code"):
            response = guest.post("/lobby/join", json={"invite_code": room["invite_code"]})

        with allure.step("Проверяем успешный вход"):
            assert response.status_code == 200
            assert response.get_json()["room"]["players_count"] == 2

    @allure.story("Валидация запроса")
    @allure.title("Запрос без room_id и invite_code отклоняется")
    def test_join_without_identifiers(self, guest_client):
        guest, _ = guest_client

        with allure.step("Отправляем пустой запрос"):
            response = guest.post("/lobby/join", json={})

        with allure.step("Проверяем ошибку"):
            assert response.status_code == 400
            assert response.get_json()["error"] == "room_id or invite_code is required"

    @allure.story("Валидация запроса")
    @allure.title("Невалидный UUID в room_id возвращает 400")
    def test_join_invalid_room_id(self, guest_client):
        guest, _ = guest_client

        with allure.step("Отправляем мусор в room_id"):
            response = guest.post("/lobby/join", json={"room_id": "not-a-uuid"})

        with allure.step("Проверяем ошибку"):
            assert response.status_code == 400
            assert response.get_json()["error"] == "invalid room_id"

    @allure.story("Несуществующая комната")
    @allure.title("Вход в несуществующую комнату возвращает 404")
    def test_join_unknown_room(self, guest_client):
        guest, _ = guest_client

        with allure.step("Отправляем существующий формат UUID, но несуществующую комнату"):
            response = guest.post("/lobby/join", json={
                "room_id": "00000000-0000-0000-0000-000000000000",
            })

        with allure.step("Проверяем 404"):
            assert response.status_code == 404
            assert response.get_json()["error"] == "room not found"

    @allure.story("Несуществующая комната")
    @allure.title("Неверный invite_code возвращает 404")
    def test_join_unknown_invite_code(self, guest_client):
        guest, _ = guest_client

        with allure.step("Отправляем заведомо несуществующий код"):
            response = guest.post("/lobby/join", json={"invite_code": "ZZZZZZZZ"})

        with allure.step("Проверяем 404"):
            assert response.status_code == 404

    @allure.story("Один пользователь — одна комната")
    @allure.title("Пользователь не может войти во вторую комнату")
    def test_join_when_already_in_other_room(self, owner_client, guest_client, third_client):
        owner, _ = owner_client
        guest, _ = guest_client
        third, _ = third_client

        with allure.step("Владелец создаёт комнату A"):
            room_a = _create_room(owner)
        with allure.step("Третий игрок создаёт комнату B"):
            room_b = _create_room(third)

        with allure.step("Второй игрок входит в A"):
            ok = guest.post("/lobby/join", json={"room_id": room_a["id"]})
            assert ok.status_code == 200

        with allure.step("Тот же игрок пробует войти в B"):
            response = guest.post("/lobby/join", json={"room_id": room_b["id"]})

        with allure.step("Проверяем 409"):
            assert response.status_code == 409
            assert response.get_json()["error"] == "user already in a room"

    @allure.story("Идемпотентность")
    @allure.title("Повторный вход в свою же комнату возвращает 200, без дубликатов")
    def test_join_same_room_twice_is_idempotent(self, owner_client, guest_client):
        owner, _ = owner_client
        guest, _ = guest_client

        with allure.step("Владелец создаёт комнату"):
            room = _create_room(owner)

        with allure.step("Второй игрок входит дважды"):
            first = guest.post("/lobby/join", json={"room_id": room["id"]})
            second = guest.post("/lobby/join", json={"room_id": room["id"]})

        with allure.step("Проверяем, что второй вход тоже 200 и игроков по-прежнему 2"):
            assert first.status_code == 200
            assert second.status_code == 200
            assert second.get_json()["room"]["players_count"] == 2

    @allure.story("Заполненная комната")
    @allure.title("В полностью заполненную комнату войти нельзя")
    def test_join_full_room(self, app, owner_client, guest_client):
        owner, _ = owner_client
        guest, _ = guest_client

        with allure.step("Владелец создаёт комнату на 2 игрока"):
            room = _create_room(owner, max_players=2)

        with allure.step("Второй игрок занимает оставшееся место"):
            response = guest.post("/lobby/join", json={"room_id": room["id"]})
            assert response.status_code == 200

        with allure.step("Третий клиент пробует войти"):
            third = app.test_client()
            reg = third.post("/auth/register", json={
                "username": "extra_player",
                "password": "qwerty123",
            })
            assert reg.status_code == 201
            response = third.post("/lobby/join", json={"room_id": room["id"]})

        with allure.step("Проверяем 409 room is full"):
            assert response.status_code == 409
            assert response.get_json()["error"] == "room is full"

    @allure.story("Авторизация")
    @allure.title("Неавторизованный пользователь не может войти в комнату")
    def test_join_requires_auth(self, client, owner_client):
        owner, _ = owner_client

        with allure.step("Владелец создаёт комнату"):
            room = _create_room(owner)

        with allure.step("Анонимный клиент пытается войти"):
            response = client.post("/lobby/join", json={"room_id": room["id"]})

        with allure.step("Проверяем, что доступ запрещён"):
            assert response.status_code == 401
