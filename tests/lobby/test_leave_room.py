import uuid

import allure

from app.models import Room, RoomPlayer


def _create_room(client, **kwargs):
    response = client.post("/lobby/create", json=kwargs)
    assert response.status_code == 201, response.get_json()
    return response.get_json()["room"]


@allure.epic("Лобби")
@allure.feature("Выход из комнаты")
class TestLeaveRoom:

    @allure.story("Успешный выход")
    @allure.title("Игрок выходит из комнаты, в которой не он один — комната остаётся")
    def test_leave_keeps_room_when_others_remain(self, app, owner_client, guest_client):
        owner, _ = owner_client
        guest, _ = guest_client

        with allure.step("Создаём комнату и приглашаем второго игрока"):
            room = _create_room(owner)
            guest.post("/lobby/join", json={"room_id": room["id"]})

        with allure.step("Второй игрок выходит"):
            response = guest.post("/lobby/leave", json={})

        with allure.step("Проверяем успешный ответ"):
            assert response.status_code == 200
            assert response.get_json()["status"] == "ok"

        with allure.step("В БД комната ещё существует, а гость в ней не числится"):
            room_uuid = uuid.UUID(room["id"])
            with app.app_context():
                assert Room.query.filter_by(id=room_uuid).first() is not None
                assert RoomPlayer.query.filter_by(room_id=room_uuid).count() == 1

    @allure.story("Удаление пустой комнаты")
    @allure.title("После выхода последнего игрока комната удаляется")
    def test_leave_deletes_empty_room(self, app, owner_client):
        owner, _ = owner_client

        with allure.step("Владелец создаёт комнату"):
            room = _create_room(owner)

        with allure.step("Владелец сам же из неё выходит"):
            response = owner.post("/lobby/leave", json={})
            assert response.status_code == 200

        with allure.step("Проверяем, что комната удалена из БД"):
            room_uuid = uuid.UUID(room["id"])
            with app.app_context():
                assert Room.query.filter_by(id=room_uuid).first() is None
                assert RoomPlayer.query.filter_by(room_id=room_uuid).count() == 0

    @allure.story("Валидация запроса")
    @allure.title("Выход с невалидным room_id возвращает 400")
    def test_leave_invalid_room_id(self, owner_client):
        owner, _ = owner_client

        with allure.step("Создаём комнату, чтобы пользователь в ней состоял"):
            _create_room(owner)

        with allure.step("Отправляем мусор вместо UUID"):
            response = owner.post("/lobby/leave", json={"room_id": "not-a-uuid"})

        with allure.step("Проверяем ошибку"):
            assert response.status_code == 400
            assert response.get_json()["error"] == "invalid room_id"

    @allure.story("Пользователь не в комнате")
    @allure.title("Выход без членства возвращает 404")
    def test_leave_when_not_in_room(self, owner_client):
        owner, _ = owner_client

        with allure.step("Пользователь, не вступивший в комнату, пробует выйти"):
            response = owner.post("/lobby/leave", json={})

        with allure.step("Проверяем 404"):
            assert response.status_code == 404
            assert response.get_json()["error"] == "user is not in a room"

    @allure.story("Авторизация")
    @allure.title("Неавторизованный пользователь не может вызвать /leave")
    def test_leave_requires_auth(self, client):
        with allure.step("Анонимный запрос"):
            response = client.post("/lobby/leave", json={})

        with allure.step("Проверяем, что доступ запрещён"):
            assert response.status_code == 401
