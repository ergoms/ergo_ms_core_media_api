# Media API

Отдельный сервис для хранения и раздачи файлов. Основной Django API **не** отдаёт пользовательские файлы по `/media/`.

Проверка прав и подписанные URL реализованы здесь, а не в основном API. Так проще изолировать доступ к файлам и не смешивать медиа с остальными эндпоинтами сервера.

Запуск: `ergoms start-media`. Порт по умолчанию — **8003** (`MEDIA_API_BIND_PORT` в [`env/media.env.example`](../../env/media.env.example)). Режим доступа ядра к файлам — `ERGO_MEDIA=local|remote` в корневом `.env`. Подробности — [`.docs/development.md`](../../.docs/development.md). Оглавление документации — в [корневом README](../../README.md#документация).

## Структура

| Каталог | Назначение |
|---------|------------|
| `src/media_server/` | views, квоты загрузки, подпись URL, settings, storage |
| `tests/` | проверки IP, валидации контента, локального хранения |

Серверная часть ядра, которая вызывает media_api: `core/api/src/core/utils/media_client/`, `media_signing.py`. Общая HMAC-логика подписи — `core/shared/media_hmac.py`. Точка входа процесса — `core/api/scripts/start_media_api.py`.

Ключи `MEDIA_API_*`, пути и лимиты загрузок — [`env/media.env.example`](../../env/media.env.example). Зоны по префиксу пути — локальный `media_zones.yaml` в корне (образец [`media_zones.yaml.example`](../../media_zones.yaml.example), в git его нет): `remote` (другой media_api) или `local` (каталог на другом диске). Пустой адрес удалённой зоны её выключает. Перенос уже лежащих файлов: `ergoms api relocate_media_zone`. За nginx смотрите прокси в [`env/nginx.env.example`](../../env/nginx.env.example) ([`.cursor/rules/deployment-infra.mdc`](../../.cursor/rules/deployment-infra.mdc)); публичный URL media — `MEDIA_API_URL` или `MEDIA_API_HOST` / `MEDIA_API_PROTOCOL` во фрагменте media.

## Правила для разработчиков

| Тема | Правило |
|------|---------|
| Загрузка и отдача файлов | [`.cursor/rules/media_api.mdc`](../../.cursor/rules/media_api.mdc) |
| Шаблоны `.env` | [`.cursor/rules/env-examples.mdc`](../../.cursor/rules/env-examples.mdc) |
| Квоты upload (контракты) | [`.cursor/rules/module-contracts.mdc`](../../.cursor/rules/module-contracts.mdc) |
| Безопасность | [`.cursor/rules/security.mdc`](../../.cursor/rules/security.mdc) |
| Redis, nginx (prod) | [`.cursor/rules/deployment-infra.mdc`](../../.cursor/rules/deployment-infra.mdc) |

## Связанные части ядра

- Сервер: [`../api/README.md`](../api/README.md)
- Клиент: [`../client/README.md`](../client/README.md)
- Развёртывание: [`../deployment/logic.md`](../deployment/logic.md)
