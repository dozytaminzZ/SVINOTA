import allure
import pytest

from app.models import User


@allure.epic("Авторизация")
@allure.feature("Регистрация пользователя")
class TestRegister:

    @allure.story("Успешная регистрация нового пользователя")
    @allure.title("Регистрация с корректными данными возвращает 201 и тело пользователя")
    def test_register_success(self, client, app):
        with allure.step("Готовим валидные данные для регистрации"):
            payload = {
                "username": "newbie",
                "password": "secret123",
                "email": "newbie@example.com",
            }

        with allure.step("Отправляем POST /auth/register"):
            response = client.post("/auth/register", json=payload)

        with allure.step("Проверяем, что статус 201 Created"):
            assert response.status_code == 201

        with allure.step("Проверяем структуру ответа"):
            data = response.get_json()
            assert data["status"] == "ok"
            assert data["user"]["username"] == "newbie"
            assert data["user"]["email"] == "newbie@example.com"
            assert data["user"]["wins"] == 0
            assert data["user"]["losses"] == 0
            assert "id" in data["user"]

        with allure.step("Проверяем, что пользователь действительно сохранён в БД"):
            with app.app_context():
                user = User.query.filter_by(username="newbie").first()
                assert user is not None
                assert user.email == "newbie@example.com"
                assert user.password_hash is not None
                assert user.password_hash != "secret123", "Пароль должен храниться в виде хэша"

    @allure.story("Успешная регистрация нового пользователя")
    @allure.title("Регистрация без email допустима")
    def test_register_without_email(self, client):
        with allure.step("Отправляем регистрацию без поля email"):
            response = client.post("/auth/register", json={
                "username": "noemail",
                "password": "secret123",
            })

        with allure.step("Проверяем, что регистрация прошла успешно"):
            assert response.status_code == 201
            data = response.get_json()
            assert data["user"]["email"] is None

    @allure.story("Валидация данных при регистрации")
    @allure.title("Регистрация без username возвращает 400")
    def test_register_missing_username(self, client):
        with allure.step("Отправляем запрос без username"):
            response = client.post("/auth/register", json={"password": "secret123"})

        with allure.step("Проверяем, что вернулась ошибка 400"):
            assert response.status_code == 400
            assert response.get_json()["error"] == "username and password are required"

    @allure.story("Валидация данных при регистрации")
    @allure.title("Регистрация без пароля возвращает 400")
    def test_register_missing_password(self, client):
        with allure.step("Отправляем запрос без password"):
            response = client.post("/auth/register", json={"username": "somebody"})

        with allure.step("Проверяем, что вернулась ошибка 400"):
            assert response.status_code == 400
            assert response.get_json()["error"] == "username and password are required"

    @allure.story("Валидация данных при регистрации")
    @allure.title("Слишком короткий пароль отклоняется")
    def test_register_password_too_short(self, client):
        with allure.step("Отправляем запрос с паролем короче 6 символов"):
            response = client.post("/auth/register", json={
                "username": "shortpass",
                "password": "123",
            })

        with allure.step("Проверяем, что вернулась ошибка про длину пароля"):
            assert response.status_code == 400
            assert response.get_json()["error"] == "password too short"

    @allure.story("Валидация данных при регистрации")
    @allure.title("Слишком длинный username отклоняется")
    def test_register_username_too_long(self, client):
        with allure.step("Готовим username длиннее 50 символов"):
            long_username = "u" * 51

        with allure.step("Отправляем запрос с длинным username"):
            response = client.post("/auth/register", json={
                "username": long_username,
                "password": "secret123",
            })

        with allure.step("Проверяем, что вернулась ошибка про длину username"):
            assert response.status_code == 400
            assert response.get_json()["error"] == "username too long"

    @allure.story("Защита от дубликатов")
    @allure.title("Регистрация с уже занятым username отклоняется")
    def test_register_duplicate_username(self, client, registered_user):
        with allure.step("Пробуем зарегистрироваться с уже существующим username"):
            response = client.post("/auth/register", json={
                "username": registered_user["username"],
                "password": "anotherpass",
                "email": "other@example.com",
            })

        with allure.step("Проверяем, что получили ошибку про дубликат username"):
            assert response.status_code == 400
            assert response.get_json()["error"] == "username already exists"

    @allure.story("Защита от дубликатов")
    @allure.title("Регистрация с уже занятым email отклоняется")
    def test_register_duplicate_email(self, client, registered_user):
        with allure.step("Пробуем зарегистрировать нового пользователя с тем же email"):
            response = client.post("/auth/register", json={
                "username": "another_user",
                "password": "secret123",
                "email": registered_user["email"],
            })

        with allure.step("Проверяем, что получили ошибку про дубликат email"):
            assert response.status_code == 400
            assert response.get_json()["error"] == "email already exists"

    @allure.story("Защита от повторной регистрации")
    @allure.title("Уже залогиненный пользователь не может зарегистрироваться повторно")
    def test_register_when_already_authenticated(self, client):
        with allure.step("Регистрируем пользователя (он автоматически авторизуется)"):
            first = client.post("/auth/register", json={
                "username": "firsty",
                "password": "secret123",
            })
            assert first.status_code == 201

        with allure.step("Из той же сессии пытаемся зарегистрироваться ещё раз"):
            second = client.post("/auth/register", json={
                "username": "secondy",
                "password": "secret123",
            })

        with allure.step("Проверяем, что повторная регистрация отклонена"):
            assert second.status_code == 400
            assert second.get_json()["error"] == "already authenticated"
