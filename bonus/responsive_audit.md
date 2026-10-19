# Отчёт по тестированию адаптивности (360 px) и кроссбраузерности (Safari / WebKit)

## 1. Введение
Согласно разделу 2 ТЗ:
> «Адаптив: Корректно отображается на ширине от 360 px, без горизонтального скролла. Браузеры — последние версии Chrome, Safari, Firefox.»

В ходе тестирования были проверены мобильные вьюпорты (360×640 px, 360×800 px, 375×667 px — iPhone SE, 390×844 px — iPhone 13/14/15/16) на движках Blink (Chrome), Gecko (Firefox) и WebKit (Safari).

---

## 2. Результаты тестирования на ширине 360 px

### ❌ БАГ: Появление горизонтального скролла на ширине 360 px (BUG-11)
- **Фактическое поведение:**
  При ширине окна 360 px страница имеет горизонтальную полосу прокрутки. Ширина контента `document.documentElement.scrollWidth` составляет **396 px**, в то время как ширина видимой области `clientWidth` равна **360 px** (переполнение на 360 px + 36 px контента).
- **Причина в коде:**
  В файле стилей `index.html` (строка 54):
  ```css
  aside {
    position: sticky;
    top: 16px;
    min-width: 380px; /* <--- КРИТИЧЕСКАЯ ОШИБКА */
  }
  ```
  И в медиа-запросе (строка 69):
  ```css
  @media (max-width: 860px) {
    .grid { grid-template-columns: 1fr; }
    .tariffs, .methods { grid-template-columns: 1fr; }
  }
  ```
  Хотя сетка перестраивается в одну колонку (`grid-template-columns: 1fr`), свойство `min-width: 380px` у блока `aside` не сбрасывается. Поскольку 380 px > 360 px, правая часть карточки «Итого» вылезает за пределы экрана.
- **Подтверждение автотестом:**
  Автотест Playwright `test_ui_form.py::test_viewport_360px_no_horizontal_scroll` зафиксировал:
  `AssertionError: BUG-11: Horizontal scroll detected on 360px! scrollWidth (396) > clientWidth (360)`.
- **Решение для разработчика:**
  Внутри медиа-запроса `@media (max-width: 860px)` необходимо переопределить ширину сайдбара:
  ```css
  @media (max-width: 860px) {
    aside {
      min-width: 0;
      width: 100%;
      position: static;
    }
  }
  ```

---

## 3. Специфика отображения и дефекты в Safari (WebKit / iOS)

### 1. Позиционирование `position: sticky` на мобильных устройствах
В Safari на iOS при открытии экранной клавиатуры (при фокусе в поля ввода) `position: sticky; top: 16px;` у блока `aside` может приводить к артефактам перекрытия контента или скачкам верстки. На экранах смартфонов блок с итоговой стоимостью должен располагаться снизу формы в общем потоке (`position: static`) либо фиксироваться снизу как плавающая панель (bottom-bar).

### 2. Сглаживание шрифтов и рендеринг шрифта 'Unbounded'
В Safari (macOS и iOS) заголовки `'Unbounded'` отображаются с легким смещением базовой линии по сравнению с Blink. Рекомендуется добавить свойства:
```css
-webkit-font-smoothing: antialiased;
-moz-osx-font-smoothing: grayscale;
```

### 3. Нативный `accent-color` чекбоксов
В чекбоксах `#agree` и `#otherReceipt` используется `accent-color: var(--leaf)`. В старых версиях Safari (до iOS 15.4) данное свойство не поддерживалось, отображался стандартный синий чекбокс Apple. В современных версиях Safari 17/18 отображение корректное.

### 4. Поведение автозаполнения (Autofill / iCloud Keychain) в Safari
Поля формы содержат корректные атрибуты `autocomplete="name"`, `autocomplete="email"`, `autocomplete="tel"`, что обеспечивает удобное автозаполнение из связки ключей Safari, однако после автозаполнения в Safari фон полей перекрашивается в светло-желтый цвет через `-webkit-autofill`. Рекомендуется настроить стилизацию:
```css
input:-webkit-autofill {
  -webkit-box-shadow: 0 0 0 50px white inset;
}
```
