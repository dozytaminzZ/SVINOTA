import allure


def _create_room(client, **kwargs):
    response = client.post("/lobby/create", json=kwargs)
    assert response.status_code == 201, response.get_json()
    return response.get_json()["room"]


@allure.epic("Лобби")
@allure.feature("Готовность игрока")
class TestReady:

    @allure.story("Переключение готовности")
    @allure.title("Без флага is_ready вызов /ready инвертирует текущее значение")
    def test_ready_toggles_when_no_flag(self, owner_client):
        owner, _ = owner_client

        with allure.step("Создаём комнату — владелец автоматически не готов"):
            _create_room(owner)

        with allure.step("Первый вызов /ready без is_ready"):
            first = owner.post("/lobby/ready", json={})

        with allure.step("После переключения игрок готов, ready_count=1"):
            assert first.status_code == 200
            data = first.get_json()
            assert data["is_ready"] is True
            assert data["room"]["ready_count"] == 1

        with allure.step("Второй вызов снова инвертирует — игрок не готов"):
            second = owner.post("/lobby/ready", json={})
            data = second.get_json()
            assert data["is_ready"] is False
            assert data["room"]["ready_count"] == 0

    @allure.story("Явная установка")
    @allure.title("Передача is_ready=true устанавливает готовность")
    def test_ready_explicit_true(self, owner_client):
        owner, _ = owner_client

        with allure.step("Создаём комнату"):
            _create_room(owner)

        with allure.step("Отправляем явное is_ready=true"):
            response = owner.post("/lobby/ready", json={"is_ready": True})

        with allure.step("Проверяем, что готовность установлена"):
            assert response.status_code == 200
            assert response.get_json()["is_ready"] is True

    @allure.story("Явная установка")
    @allure.title("Передача is_ready=false сбрасывает готовность")
    def test_ready_explicit_false(self, owner_client):
        owner, _ = owner_client

        with allure.step("Создаём комнату и предварительно ставим готовность"):
            _create_room(owner)
            owner.post("/lobby/ready", json={"is_ready": True})

        with allure.step("Сбрасываем готовность явно"):
            response = owner.post("/lobby/ready", json={"is_ready": False})

        with allure.step("Проверяем, что не готов и счётчик нулевой"):
            data = response.get_json()
            assert data["is_ready"] is False
            assert data["room"]["ready_count"] == 0

    @allure.story("Счётчик ready_count")
    @allure.title("ready_count агрегирует готовность всех игроков комнаты")
    def test_ready_count_aggregates_all_players(self, owner_client, guest_client):
        owner, _ = owner_client
        guest, _ = guest_client

        with allure.step("Создаём комнату и приглашаем второго игрока"):
            room = _create_room(owner)
            guest.post("/lobby/join", json={"room_id": room["id"]})

        with allure.step("Оба игрока подтверждают готовность"):
            owner.post("/lobby/ready", json={"is_ready": True})
            response = guest.post("/lobby/ready", json={"is_ready": True})

        with allure.step("Проверяем, что ready_count=2 при players_count=2"):
            data = response.get_json()
            assert data["room"]["players_count"] == 2
            assert data["room"]["ready_count"] == 2

    @allure.story("Валидация запроса")
    @allure.title("Невалидный room_id возвращает 400")
    def test_ready_invalid_room_id(self, owner_client):
        owner, _ = owner_client

        with allure.step("Создаём комнату, чтобы пользователь был участником"):
            _create_room(owner)

        with allure.step("Отправляем невалидный room_id"):
            response = owner.post("/lobby/ready", json={"room_id": "garbage"})

        with allure.step("Проверяем ошибку"):
            assert response.status_code == 400
            assert response.get_json()["error"] == "invalid room_id"

    @allure.story("Пользователь не в комнате")
    @allure.title("/ready без членства возвращает 404")
    def test_ready_when_not_in_room(self, owner_client):
        owner, _ = owner_client

        with allure.step("Пользователь не вступал в комнату — сразу /ready"):
            response = owner.post("/lobby/ready", json={})

        with allure.step("Проверяем 404"):
            assert response.status_code == 404
            assert response.get_json()["error"] == "user is not in a room"

    @allure.story("Авторизация")
    @allure.title("Неавторизованный пользователь не может вызвать /ready")
    def test_ready_requires_auth(self, client):
        with allure.step("Анонимный запрос"):
            response = client.post("/lobby/ready", json={})

        with allure.step("Проверяем, что доступ запрещён"):
            assert response.status_code == 401
