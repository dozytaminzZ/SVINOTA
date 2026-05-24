import allure


@allure.epic("Авторизация")
@allure.feature("Сессия пользователя (logout и profile)")
class TestSession:

    @allure.story("Выход из аккаунта")
    @allure.title("Logout завершает активную сессию")
    def test_logout_after_login(self, client, registered_user):
        with allure.step("Логинимся"):
            login = client.post("/auth/login", json={
                "username": registered_user["username"],
                "password": registered_user["password"],
            })
            assert login.status_code == 200

        with allure.step("Делаем logout"):
            logout = client.post("/auth/logout")
            assert logout.status_code == 200
            assert logout.get_json()["status"] == "ok"

        with allure.step("Проверяем, что доступ к /auth/profile закрыт"):
            profile = client.get("/auth/profile")
            assert profile.status_code == 401

    @allure.story("Выход из аккаунта")
    @allure.title("Logout анонимной сессии не падает и возвращает ok")
    def test_logout_when_not_authenticated(self, client):
        with allure.step("Вызываем logout без предварительного входа"):
            response = client.post("/auth/logout")

        with allure.step("Проверяем, что сервер вернул 200 ok"):
            assert response.status_code == 200
            assert response.get_json()["status"] == "ok"

    @allure.story("Получение профиля")
    @allure.title("Авторизованный пользователь получает свой профиль")
    def test_profile_authenticated(self, client, registered_user):
        with allure.step("Логинимся"):
            client.post("/auth/login", json={
                "username": registered_user["username"],
                "password": registered_user["password"],
            })

        with allure.step("Запрашиваем /auth/profile"):
            response = client.get("/auth/profile")

        with allure.step("Проверяем, что вернулся корректный профиль"):
            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "ok"
            assert data["user"]["username"] == registered_user["username"]
            assert data["user"]["email"] == registered_user["email"]

    @allure.story("Получение профиля")
    @allure.title("Анонимный пользователь не может получить профиль")
    def test_profile_unauthenticated(self, client):
        with allure.step("Запрашиваем /auth/profile без авторизации"):
            response = client.get("/auth/profile")

        with allure.step("Проверяем, что сервер вернул 401"):
            assert response.status_code == 401

    @allure.story("Индексный роут модуля auth")
    @allure.title("GET /auth/ возвращает статус заглушки")
    def test_auth_index(self, client):
        with allure.step("Делаем GET /auth/"):
            response = client.get("/auth/")

        with allure.step("Проверяем тело ответа"):
            assert response.status_code == 200
            assert response.get_json() == {"status": "auth module in development"}
