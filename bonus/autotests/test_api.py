import pytest
import requests

BASE_URL = "https://kvitto-qa-demo.vercel.app/api"

class TestKvittoAPI:
    """
    Автотесты API платёжного сервиса Квитто (pytest + requests).
    Проверяют соответствие контракту раздела 3 ТЗ.
    Падения тестов фиксируют расхождения стенда с ТЗ.
    """

    def test_tariffs_contract(self):
        """Проверка получения списка тарифов, заголовков и цен."""
        resp = requests.get(f"{BASE_URL}/tariffs", timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert "application/json" in resp.headers.get("Content-Type", ""), (
            f"BUG-12: Expected Content-Type application/json, got {resp.headers.get('Content-Type')}"
        )
        data = resp.json()
        assert isinstance(data, list) and len(data) == 3, "Expected 3 tariffs"
        tariffs_map = {t["id"]: t for t in data}
        assert "basic" in tariffs_map and tariffs_map["basic"]["price"] == 9900
        assert "standard" in tariffs_map and tariffs_map["standard"]["price"] == 19900
        assert "premium" in tariffs_map and tariffs_map["premium"]["price"] == 29900

    def test_payment_creation_status_201(self):
        """Проверка создания стандартного платежа и возврата статуса 201 Created."""
        payload = {
            "tariff_id": "standard",
            "name": "Иван Иванов",
            "email": "ivan@example.com",
            "phone": "+7 999 123-45-67",
            "method": "card"
        }
        resp = requests.post(f"{BASE_URL}/payments", json=payload, timeout=10)
        assert resp.status_code == 201, f"BUG-13: Expected 201 Created, got {resp.status_code}"
        data = resp.json()
        assert data.get("status") == "pending"
        assert data.get("amount") == 19900
        assert data.get("currency") == "RUB"
        assert "id" in data and isinstance(data["id"], str)

    def test_promo_discount_applied_on_backend(self):
        """Проверка применения скидки по промокоду KVITTO10 (-10%) на бэкенде."""
        payload = {
            "tariff_id": "standard",
            "name": "Петр Петров",
            "email": "petr@example.com",
            "phone": "+7 999 765-43-21",
            "method": "card",
            "promo_code": "KVITTO10"
        }
        resp = requests.post(f"{BASE_URL}/payments", json=payload, timeout=10)
        assert resp.status_code == 201, f"BUG-13: Expected 201 Created, got {resp.status_code}"
        data = resp.json()
        expected_amount = 17910  # 19900 - 10% = 17910
        assert data.get("amount") == expected_amount, (
            f"BUG-14: Backend ignored promo_code! Expected amount {expected_amount}, got {data.get('amount')}"
        )

    def test_receipt_email_preservation(self):
        """Проверка сохранения отдельного email для чека (receipt_email)."""
        payload = {
            "tariff_id": "standard",
            "name": "Анна Сидорова",
            "email": "main@example.com",
            "phone": "+7 999 000-11-22",
            "method": "sbp",
            "receipt_email": "accounting@company.ru"
        }
        resp = requests.post(f"{BASE_URL}/payments", json=payload, timeout=10)
        data = resp.json()
        assert data.get("receipt_email") == "accounting@company.ru", (
            f"BUG-15: Server overwritten receipt_email with email: {data.get('receipt_email')}"
        )

    def test_installment_invalid_months_rejected(self):
        """Проверка отклонения невалидного срока рассрочки (5 месяцев)."""
        payload = {
            "tariff_id": "standard",
            "name": "Тест Тестов",
            "email": "test@example.com",
            "phone": "+7 999 555-66-77",
            "method": "installment",
            "installment_months": 5
        }
        resp = requests.post(f"{BASE_URL}/payments", json=payload, timeout=10)
        assert resp.status_code == 422, (
            f"BUG-18: Expected 422 for invalid installment months, got {resp.status_code}"
        )

    def test_non_existent_payment_returns_404(self):
        """Проверка возврата 404 { error: 'not_found' } для несуществующего платежа."""
        resp = requests.get(f"{BASE_URL}/payments/non_existent_id_99999", timeout=10)
        assert resp.status_code == 404, f"BUG-16: Expected 404 Not Found, got {resp.status_code}"
        assert resp.json() == {"error": "not_found"}, f"Expected error not_found, got {resp.json()}"
