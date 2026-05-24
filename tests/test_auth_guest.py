import allure

from app.models import User


@allure.epic("Авторизация")
@allure.feature("Гостевой вход")
class TestGuestLogin:

    @allure.story("Создание гостевого аккаунта")
    @allure.title("Гостевой вход без параметров создаёт пользователя с префиксом guest-")
    def test_guest_default_username(self, client, app):
        with allure.step("Отправляем POST /auth/guest без тела"):
            response = client.post("/auth/guest", json={})

        with allure.step("Проверяем 201 и наличие пользователя"):
            assert response.status_code == 201
            data = response.get_json()
            assert data["status"] == "ok"
            assert data["user"]["username"].startswith("guest-")
            assert data["user"]["email"] is None

        with allure.step("Проверяем, что у гостя нет password_hash"):
            with app.app_context():
                user = User.query.filter_by(username=data["user"]["username"]).first()
                assert user is not None
                assert user.password_hash is None

    @allure.story("Создание гостевого аккаунта")
    @allure.title("Гостевой вход с кастомным base-username добавляет уникальный суффикс")
    def test_guest_custom_base_username(self, client):
        with allure.step("Отправляем гостевой вход с username=Vasya"):
            response = client.post("/auth/guest", json={"username": "Vasya"})

        with allure.step("Проверяем, что итоговый username имеет вид Vasya-<суффикс>"):
            assert response.status_code == 201
            username = response.get_json()["user"]["username"]
            assert username.startswith("Vasya-")
            assert len(username) > len("Vasya-")

    @allure.story("Уникальность гостевых имён")
    @allure.title("Два подряд гостевых входа с одним base-username создают разных пользователей")
    def test_guest_unique_usernames(self, client):
        with allure.step("Первый гостевой вход"):
            r1 = client.post("/auth/guest", json={"username": "duplicate"})
            assert r1.status_code == 201
            first_username = r1.get_json()["user"]["username"]

        with allure.step("Сбрасываем сессию"):
            client.post("/auth/logout")

        with allure.step("Второй гостевой вход с тем же базовым именем"):
            r2 = client.post("/auth/guest", json={"username": "duplicate"})
            assert r2.status_code == 201
            second_username = r2.get_json()["user"]["username"]

        with allure.step("Проверяем, что username-ы разные"):
            assert first_username != second_username

    @allure.story("Защита от повторного входа")
    @allure.title("Авторизованный пользователь не может зайти ещё раз как гость")
    def test_guest_when_already_authenticated(self, client):
        with allure.step("Создаём первого гостя"):
            first = client.post("/auth/guest", json={})
            assert first.status_code == 201

        with allure.step("Пытаемся создать второго гостя в той же сессии"):
            second = client.post("/auth/guest", json={})

        with allure.step("Проверяем, что вернулась ошибка already authenticated"):
            assert second.status_code == 400
            assert second.get_json()["error"] == "already authenticated"
