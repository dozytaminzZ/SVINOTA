import allure


@allure.epic("Авторизация")
@allure.feature("Вход пользователя")
class TestLogin:

    @allure.story("Успешный вход")
    @allure.title("Вход по username и паролю проходит успешно")
    def test_login_by_username(self, client, registered_user):
        with allure.step("Отправляем POST /auth/login с username и паролем"):
            response = client.post("/auth/login", json={
                "username": registered_user["username"],
                "password": registered_user["password"],
            })

        with allure.step("Проверяем, что вход прошёл успешно"):
            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "ok"
            assert data["user"]["username"] == registered_user["username"]

    @allure.story("Успешный вход")
    @allure.title("Вход по email и паролю проходит успешно")
    def test_login_by_email(self, client, registered_user):
        with allure.step("Отправляем POST /auth/login с email и паролем"):
            response = client.post("/auth/login", json={
                "email": registered_user["email"],
                "password": registered_user["password"],
            })

        with allure.step("Проверяем, что вход прошёл успешно"):
            assert response.status_code == 200
            data = response.get_json()
            assert data["user"]["email"] == registered_user["email"]

    @allure.story("Валидация данных входа")
    @allure.title("Вход без пароля возвращает 400")
    def test_login_missing_password(self, client, registered_user):
        with allure.step("Отправляем запрос без password"):
            response = client.post("/auth/login", json={
                "username": registered_user["username"],
            })

        with allure.step("Проверяем ошибку 400"):
            assert response.status_code == 400
            assert response.get_json()["error"] == "username or email and password are required"

    @allure.story("Валидация данных входа")
    @allure.title("Вход без username и email возвращает 400")
    def test_login_missing_identity(self, client):
        with allure.step("Отправляем запрос с одним только password"):
            response = client.post("/auth/login", json={"password": "secret123"})

        with allure.step("Проверяем ошибку 400"):
            assert response.status_code == 400

    @allure.story("Неверные учётные данные")
    @allure.title("Неверный пароль возвращает 401")
    def test_login_wrong_password(self, client, registered_user):
        with allure.step("Отправляем запрос с правильным username, но неверным паролем"):
            response = client.post("/auth/login", json={
                "username": registered_user["username"],
                "password": "totally-wrong",
            })

        with allure.step("Проверяем, что вернулся 401 и сообщение invalid credentials"):
            assert response.status_code == 401
            assert response.get_json()["error"] == "invalid credentials"

    @allure.story("Неверные учётные данные")
    @allure.title("Вход несуществующего пользователя возвращает 401")
    def test_login_unknown_user(self, client):
        with allure.step("Отправляем запрос с username, которого нет в БД"):
            response = client.post("/auth/login", json={
                "username": "ghost_user",
                "password": "secret123",
            })

        with allure.step("Проверяем 401 invalid credentials"):
            assert response.status_code == 401
            assert response.get_json()["error"] == "invalid credentials"

    @allure.story("Неверные учётные данные")
    @allure.title("Гостевой пользователь не может войти по паролю")
    def test_login_guest_account_has_no_password(self, client):
        with allure.step("Создаём гостя"):
            guest = client.post("/auth/guest", json={"username": "guesty"})
            assert guest.status_code == 201
            guest_username = guest.get_json()["user"]["username"]

        with allure.step("Сбрасываем сессию"):
            client.post("/auth/logout")

        with allure.step("Пробуем залогиниться под именем гостя с любым паролем"):
            response = client.post("/auth/login", json={
                "username": guest_username,
                "password": "anything",
            })

        with allure.step("Проверяем, что вход отклонён"):
            assert response.status_code == 401
            assert response.get_json()["error"] == "invalid credentials"

    @allure.story("Защита от повторного входа")
    @allure.title("Уже авторизованный пользователь не может войти снова")
    def test_login_when_already_authenticated(self, client, registered_user):
        with allure.step("Первый успешный вход"):
            first = client.post("/auth/login", json={
                "username": registered_user["username"],
                "password": registered_user["password"],
            })
            assert first.status_code == 200

        with allure.step("Повторный вход в той же сессии"):
            second = client.post("/auth/login", json={
                "username": registered_user["username"],
                "password": registered_user["password"],
            })

        with allure.step("Проверяем, что вернулась ошибка already authenticated"):
            assert second.status_code == 400
            assert second.get_json()["error"] == "already authenticated"
