import pytest
from playwright.sync_api import Page, expect

STAND_URL = "https://kvitto-qa-demo.vercel.app"

class TestKvittoUI:
    """
    E2E автотесты платёжной формы Квитто (Playwright).
    Проверяют соответствие интерфейса разделу 2 ТЗ (цены, скидки, валидация, оферта, адаптив).
    """

    def test_default_state(self, page: Page):
        """Проверка дефолтного состояния: выбран тариф Стандарт, сумма 19 900 ₽."""
        page.goto(STAND_URL)
        standard_btn = page.locator(".tariff[data-t='standard']")
        expect(standard_btn).to_have_class("tariff active")
        expect(page.locator("#sTotal")).to_have_text("19 900 ₽")
        expect(page.locator("#pay")).to_have_text("Оплатить 19 900 ₽")

    def test_premium_tariff_price_override_bug(self, page: Page):
        """Проверка соответствия цены тарифа Премиум (ТЗ: 29 900 ₽). Ловит BUG-08."""
        page.goto(STAND_URL)
        page.click(".tariff[data-t='premium']")
        # По ТЗ: в «Итого» и на кнопке сумма должна быть 29 900 ₽
        expect(page.locator("#sTotal")).to_have_text("29 900 ₽")
        expect(page.locator("#pay")).to_have_text("Оплатить 29 900 ₽")

    def test_installment_6_months_calculation(self, page: Page):
        """Проверка расчёта ежемесячного платежа рассрочки на 6 месяцев (ТЗ: 19900/6 = 3317 ₽). Ловит BUG-02."""
        page.goto(STAND_URL)
        page.click(".method[data-m='installment']")
        page.click(".months button[data-n='6']")
        note_text = page.locator("#instNote").inner_text()
        assert "3 317 ₽" in note_text, f"BUG-02: Expected 3 317 ₽/mo, got: {note_text}"

    def test_promo_case_insensitivity(self, page: Page):
        """Проверка применения промокода в нижнем регистре (ТЗ: регистр не важен). Ловит BUG-03."""
        page.goto(STAND_URL)
        page.fill("#promo", "kvitto10")
        page.click("#applyPromo")
        expect(page.locator("#promoOk")).to_have_text("Промокод применён: −10%")
        expect(page.locator("#err-promo")).to_be_empty()

    def test_offer_checkbox_blocks_payment(self, page: Page):
        """Проверка блокировки кнопки «Оплатить», пока не проставлена галочка оферты. Ловит BUG-06."""
        page.goto(STAND_URL)
        agree_checkbox = page.locator("#agree")
        pay_btn = page.locator("#pay")
        assert not agree_checkbox.is_checked()
        # По ТЗ: пока галочка не стоит, кнопка оплаты неактивна
        assert pay_btn.is_disabled(), "BUG-06: Pay button is active without accepting offer!"

    def test_viewport_360px_no_horizontal_scroll(self, page: Page):
        """Проверка адаптива на ширине 360 px без горизонтального скролла. Ловит BUG-11."""
        page.set_viewport_size({"width": 360, "height": 800})
        page.goto(STAND_URL)
        page.wait_for_load_state("networkidle")
        scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
        client_width = page.evaluate("() => document.documentElement.clientWidth")
        assert scroll_width <= client_width, (
            f"BUG-11: Horizontal scroll detected on 360px! scrollWidth ({scroll_width}) > clientWidth ({client_width})"
        )
