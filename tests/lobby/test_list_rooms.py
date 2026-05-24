import allure


def _create_room(client, **kwargs):
    response = client.post("/lobby/create", json=kwargs)
    assert response.status_code == 201, response.get_json()
    return response.get_json()["room"]


@allure.epic("Лобби")
@allure.feature("Список комнат")
class TestListRooms:

    @allure.story("Пустой список")
    @allure.title("Когда комнат нет — возвращается пустой список")
    def test_empty_list(self, client):
        with allure.step("Запрашиваем список без созданных комнат"):
            response = client.get("/lobby/rooms")

        with allure.step("Проверяем структуру ответа"):
            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "ok"
            assert data["rooms"] == []

    @allure.story("Публичные комнаты")
    @allure.title("По умолчанию возвращаются только публичные комнаты")
    def test_default_returns_only_public(self, client, owner_client, guest_client):
        owner, _ = owner_client
        guest, _ = guest_client

        with allure.step("Создаём публичную и приватную комнаты"):
            public_room = _create_room(owner, is_private=False)
            _create_room(guest, is_private=True)

        with allure.step("Запрашиваем список с дефолтными параметрами"):
            response = client.get("/lobby/rooms")

        with allure.step("Проверяем, что отдана только публичная комната"):
            assert response.status_code == 200
            rooms = response.get_json()["rooms"]
            assert len(rooms) == 1
            assert rooms[0]["id"] == public_room["id"]
            assert rooms[0]["is_private"] is False

    @allure.story("Все комнаты")
    @allure.title("С public_only=0 возвращаются и приватные тоже")
    def test_public_only_off_returns_all(self, client, owner_client, guest_client):
        owner, _ = owner_client
        guest, _ = guest_client

        with allure.step("Создаём публичную и приватную комнаты"):
            _create_room(owner, is_private=False)
            _create_room(guest, is_private=True)

        with allure.step("Запрашиваем список с public_only=0"):
            response = client.get("/lobby/rooms?public_only=0")

        with allure.step("Проверяем, что вернулись обе"):
            assert response.status_code == 200
            rooms = response.get_json()["rooms"]
            assert len(rooms) == 2

    @allure.story("Содержимое payload")
    @allure.title("Каждая запись комнаты содержит ожидаемые поля и актуальные счётчики")
    def test_room_payload_fields(self, client, owner_client, guest_client):
        owner, _ = owner_client
        guest, _ = guest_client

        with allure.step("Владелец создаёт комнату, второй игрок входит и готов"):
            room = _create_room(owner, max_players=4)
            guest.post("/lobby/join", json={"room_id": room["id"]})
            guest.post("/lobby/ready", json={"is_ready": True})

        with allure.step("Получаем список комнат"):
            response = client.get("/lobby/rooms")

        with allure.step("Проверяем, что в payload есть все ожидаемые поля и счётчики"):
            assert response.status_code == 200
            rooms = response.get_json()["rooms"]
            assert len(rooms) == 1
            item = rooms[0]
            for field in (
                "id", "owner_id", "invite_code", "status",
                "max_players", "players_count", "ready_count", "is_private",
            ):
                assert field in item, f"missing field {field}"
            assert item["players_count"] == 2
            assert item["ready_count"] == 1
            assert item["max_players"] == 4
            assert item["status"] == "waiting"
