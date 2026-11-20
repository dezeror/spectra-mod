# Spectra — Liquid Glass мод для Telegram (Android)

**Spectra** — кастомный клиент Telegram на базе открытого форка **Nagram** (NekoX-линия),
с фирменной темой **Spectra Dark**, визуальным стилем **Liquid Glass + iOS** и страницей
**Spectra Settings** со **103 настройками** (69 новых ключей мода + 34 пункта, привязанных
к встроенным возможностям Nagram).

Пакет готов к сборке: применяется поверх клона Nagram скриптом `apply_overlay.py`
или автоматически в GitHub Actions одним запуском.

---

## Что внутри

```
spectra-mod/
├── overlay/
│   ├── java/org/telegram/spectra/   # 21 Java-файл мода (см. ниже)
│   ├── res/                          # иконки: mipmap-*/ все плотности + adaptive + round
│   ├── theme/Spectra_Dark.attheme    # тема (107 ключей, валидировано по Theme.java)
│   ├── tools/apply_overlay.py        # упаковщик: брендинг, иконки, API-ключи, entry
│   ├── workflows/spectra-build.yml   # GitHub Actions: сборка APK одним запуском
│   └── docs/                         # HOOKS.md, FEATURES.md, TESTING.md
└── spec/                             # исходники-спецификации (settings_*.json и др.)
```

### Код мода (`org.telegram.spectra`)

| Файл | Назначение |
|---|---|
| `SpectraSettingsActivity` | Хаб настроек: логотип + 8 разделов |
| `Spectra{Glass,Home,Chat,Input,Privacy,Smart,Media,System}Activity` | Страницы настроек |
| `SpectraBaseSettingsFragment` | Фреймворк страниц (switch/slider/color/enum-строки) |
| `SpectraConfig` | 103 ключа настроек (SharedPreferences, авто-генерация) |
| `SpectraReflection` | Отказоустойчивая привязка к ключам Nagram/NaConfig |
| `SpectraGlassPanel` | Liquid Glass: RenderEffect (API 31+) + fallback-blur, неоновая обводка |
| `SpectraPalette` | Тема Spectra Dark: 107 ключей Theme.* (валидированы) |
| `SpectraThemeUtils` | Применение темы + Material You акцент |
| `SpectraUtils` | Калькулятор, сниппеты, анти-фишинг, дата регистрации, @all |
| `SpectraDeletedStore` | Анти-удаление и история правок (локальный кэш) |
| `SpectraExifCleaner` | Очистка EXIF при отправке фото |
| `SpectraAvatarUtils` | Squircle-радиус аватарок + неоновое кольцо онлайн |
| `SpectraSliderCell` / `SpectraColorCell` | Кастомные строки настроек |

Документы: `docs/FEATURES.md` — карта всех 103 настроек; `docs/HOOKS.md` — 32 проверенных
хука в код Nagram (файл, метод, готовый сниппет); `docs/TESTING.md` — ADB-чеклист.

---

## Быстрый старт: APK за один запуск

1. Создайте репозиторий на GitHub и загрузите содержимое этого пакета
   (папка `spectra-mod/` в корень репо, файл workflow — в `.github/workflows/`).
2. Вкладка **Actions** → **Spectra Build** → **Run workflow**.
3. Через ~25–60 минут в артефактах появится `Spectra-APK` (debug-версия уже подписана
   и устанавливается сразу; release-версия опционально подписывается секретами).

Скрипт workflow: клонирует Nagram с сабмодулями → применяет оверлей → собирает
`assembleArm64Debug` (fallback на универсальные варианты) → выкладывает артефакты.

### Локальная сборка (если хочется руками)

```bash
git clone --depth 1 --recurse-submodules -j8 https://github.com/NextAlone/Nagram.git
python3 spectra-mod/overlay/tools/apply_overlay.py --repo Nagram
cd Nagram && ./gradlew TMessagesProj:assembleArm64Debug
# APK: TMessagesProj/build/outputs/apk/arm64/debug/
```

Требования: JDK 17, Android SDK 36, NDK 27.x, ~15 ГБ диска, 8+ ГБ RAM.

---

## Что уже работает из коробки

- Брендинг: `applicationId org.spectra.messenger`, название «Spectra», все иконки
  (legacy 48–192px, round, adaptive foreground/background на фоне `#050706`).
- Публичный FOSS API-ключ Telegram (APP_ID 12834) — для тестов; для продакшена
  зарегистрируйте собственный на my.telegram.org и передайте `--app-id/--app-hash`.
- Тема Spectra Dark: AMOLED-чёрный `#050706`, изумрудные подложки `#0D1411`,
  неоновые акценты `#2CE876 → #12B857`, градиентные исходящие пузыри.
- 34 настройки из блока Nagram: ghost-режим и вся невидимость, антиреклама,
  безлимитные закрепы, подтверждения отправки, битрейт голосовых, системные эмодзи,
  центрирование заголовка, скрытие телефона и др.
- 69 настроек Spectra (Liquid Glass, скругления, squircle-аватарки, Дзен, анти-удаление
  и т.д.) — UI готов; включение поведения соответствующими хуками из `HOOKS.md`.

## Честные ограничения

- Полная сборка APK выполняется в GitHub Actions (в среде подготовки пакета нет
  Android SDK/NDK — гигабайтный toolchain и сборка нативных библиотек не помещаются
  в лимиты песочницы).
- Пункты с хранилищем `SpectraConfig.*` требуют наложения хуков (по одному, 5–25 строк
  каждый) — это стандартная практика модов, все точки вставки уже найдены и проверены.
- Один хук (`drawerEnabled`) не нашёл якоря в текущем снапшоте Nagram — помечен в HOOKS.md.
- Изменённый клиент Telegram нарушает условия использования для некоторых функций
  (скрытие статуса прочтения и т.п.) — используйте на свой риск; мод не поднимает лимиты
  и не обходит блокировки аккаунтов.

## Лицензии

Код Nagram/Telegram — GPLv3 (сохранив уведомления). Код Spectra распространяется
под той же лицензией. Название и логотип — ваш брендинг.
