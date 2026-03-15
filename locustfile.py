import sys
import requests
from locust import HttpUser, task, between, events

# Глобальна змінна для токена, щоб не "ддосити" логін
GLOBAL_TOKEN = None

# Цей івент запускається ОДИН РАЗ до того, як почнуть створюватися юзери
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global GLOBAL_TOKEN
    print("🔑 Отримуємо токен для стрес-тесту...")
    
    # Використовуй свій реальний шлях та кредо
    response = requests.post("http://localhost:8000/v1/auth/token", data={
        "username": "test_user_1",
        "password": "securepassword123"
    })
    
    if response.status_code == 200:
        GLOBAL_TOKEN = response.json().get("access_token")
        print("✅ Токен успішно отримано! Запускаємо юзерів...")
    else:
        print(f"❌ Критична помилка логіну: {response.text}")
        sys.exit(1) # Зупиняємо тест, якщо токена немає

class ChatMemoryTester(HttpUser):
    wait_time = between(0.5, 1.0)
    
    # Встав свій реальний ID чату
    TARGET_CHAT_ID = "f187f617-c81c-4d67-a38d-fcc35e57d1e3" 

    def on_start(self):
        # Всі 1000 юзерів беруть готовий токен, не смикаючи бекенд
        self.headers = {"Authorization": f"Bearer {GLOBAL_TOKEN}"}

    @task
    def load_chat_context(self):
        with self.client.get(
            f"/LLM/chat/{self.TARGET_CHAT_ID}/history_test",
            headers=self.headers,
            name="Load Chat History",
            catch_response=True  # Щоб юзер не вмирав від 500-х помилок сервера
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code} - {response.text}")