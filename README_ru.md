# Бот: сбор ставок с Novig, Hedgehog Markets, Augur → Excel

## Возможности
- Команда `/fetch augur|hedgehog|novig|all` — собирает данные и шлёт вам Excel-файлы.
- `Augur`: запрос по субграфу The Graph (GraphQL).
- `Hedgehog` и `Novig`: попытка извлечь данные с публичных страниц (поиск JSON-блоков `__NEXT_DATA__` / `__APOLLO_STATE__`, резерв — парсинг HTML-карточек).
- Генерация аккуратных Excel (*.xlsx) с табличками рынков.

> ⚠️ Примечание по источникам:
> - У **Augur** стабильный путь — субграф The Graph. Нужен API key The Graph (бесплатная регистрация) или можно использовать публичный эндпоинт, если доступен.
> - У **Hedgehog** и **Novig** официальной публичной документации API для анонимного доступа может не быть. В этом репо реализован «best-effort» парсинг публичных страниц. Если сайты менят разметку, возможны пустые результаты. В таком случае укажите свой собственный endpoint в `.env` (см. переменные ниже).

## Быстрый старт
1. Установите Python 3.10+
2. Установите библиотеки:
   ```bash
   pip install -r requirements.txt
   ```
3. Создайте `.env` на основе `.env.template` и укажите:
   - `BOT_TOKEN` — токен вашего Telegram-бота
   - `THE_GRAPH_API_KEY` — ключ The Graph (опционально)
   - `AUGUR_SUBGRAPH_ID` — ID субграфа Augur (по умолчанию задан популярный)
   - (опционально) `HEDGEHOG_MARKETS_URL`, `NOVIG_MARKETS_URL` — если знаете прямые JSON/GraphQL ссылки
4. Запустите бота:
   ```bash
   python main.py
   ```

## Команды
- `/start` — проверка
- `/fetch augur` — только Augur
- `/fetch hedgehog` — только Hedgehog
- `/fetch novig` — только Novig
- `/fetch all` — всё сразу

## Формат Excel
- Отдельный файл на каждую платформу в папке `./exports/` и вложением в Telegram.
- Столбцы различаются по источнику, но включают минимум: `platform`, `market_id`, `title/name`, `outcomes`, `status`, `endTime/expiration`, `liquidity/volume` (если доступно).

## Подсказки
- Если Augur отдаёт 401/403 — проверьте `THE_GRAPH_API_KEY`.
- Если Hedgehog/Novig возвращают пусто — попробуйте открыть сайты в браузере, заглянуть в DevTools → Network и найти GraphQL/REST запросы рынков. Затем укажите найденный URL в `.env`.

Удачи!