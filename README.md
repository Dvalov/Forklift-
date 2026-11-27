# Forklift Dashboard

Веб-панель оператора складского погрузчика. На вкладке «Задачи» оператор выбирает ячейки забора и доставки и следит за очередью. На вкладке «Приборы» отображаются карта склада и телеметрия погрузчика.

<img width="1919" height="958" alt="панель приборов" src="https://github.com/user-attachments/assets/3e6de0e2-13d8-474d-9340-6707d3b3e2dc" />
<img width="1919" height="952" alt="панель задач" src="https://github.com/user-attachments/assets/ebaefe81-68ce-4235-8da2-771c48a09dd8" />

---

## Стек

| Слой | Технологии |
|---|---|
| Frontend | React 19, TypeScript, Vite, TanStack Query v5, Zustand v5, Tailwind CSS |
| Backend | Django 6, Django REST Framework, django-cors-headers |
| Запуск в Docker | Docker Compose, PostgreSQL 16, Nginx |
| Интеграции | 1С для синхронизации ячеек, AnyLogic для симуляции склада и погрузчика |

---

## Архитектура

Проект состоит из трёх Django-сервисов и React-фронтенда.

```
forklift_dashboard/   → :8000  — погрузчики, задачи
Warehouse/            → :8001  — ячейки склада
Converter/            → :8002  — адрес ячейки → координаты XYZ
frontend/             → :5173  — React UI (Nginx в Docker, Vite при локальном запуске)
```

Nginx в Docker и Vite при локальном запуске проксируют запросы `/api/` к нужному сервису. Фронтенд периодически опрашивает API задач, погрузчика и ячеек, а состояние AnyLogic получает по SSE.

---

## Функциональность

**Вкладка «Задачи»**

- Создание задачи с выбором ячеек «Откуда» и «Куда»
- Синхронизация ячеек из 1С
- Очередь задач погрузчика
- История завершённых задач

**Вкладка «Приборы»**

- Карта склада с позицией погрузчика и подсветкой цели
- Спидометр, уровень заряда батареи и показания гидравлики
- Панели датчиков, состояния связи и диагностики. Часть показаний и рекомендации по скорости и заряду пока используют демонстрационные значения.

### Карта склада

После запуска откройте вкладку **«Приборы»** в нижней части интерфейса. В центре появится SVG-карта «Карта склада (вид сверху)». Голубой треугольник показывает позицию погрузчика, фиолетовая подсветка отмечает целевую ячейку, а янтарная заливка обозначает занятые ячейки.

- **С AnyLogic.** Карта строится по координатам ячеек из модели, а значок погрузчика плавно перемещается при поступлении событий через `/api/anylogic/stream`. Для ячеек, сопоставленных со складским справочником, цвет отражает доступность по данным Warehouse. Янтарная точка показывает расхождение, когда в справочнике ячейка свободна, а в симуляции занята. Для активной задачи сначала подсвечивается ячейка забора, затем ячейка доставки.
- **Без AnyLogic.** Карта показывает сетку по данным `Warehouse` и позицию погрузчика из Django. При выполнении задачи зелёным отмечаются оставшиеся точки маршрута, которые возвращает API погрузчика. При первом запуске в Docker для этого режима доступны демонстрационные ячейки.

---

## Запуск

### Docker Compose

Установите и запустите Docker Desktop или Docker Engine с плагином Compose. Выполняйте команды из корня репозитория.

1. Если корневого `.env` ещё нет, создайте его из шаблона [.env.example](.env.example).

   ```powershell
   Copy-Item .env.example .env
   ```

   В Bash используйте `cp .env.example .env`.

2. Укажите в `.env` пароль PostgreSQL (`POSTGRES_PASSWORD`) и три отдельных ключа Django (`DASHBOARD_SECRET_KEY`, `WAREHOUSE_SECRET_KEY`, `CONVERTER_SECRET_KEY`). Повторите команду генерации для каждого ключа.

   ```bash
   docker run --rm python:3.13-slim python -c "from secrets import token_urlsafe; print(token_urlsafe(50))"
   ```

   Для существующего тома PostgreSQL укажите действующий пароль роли. Изменение `POSTGRES_PASSWORD` в `.env` само по себе не меняет пароль уже созданной роли.

3. Соберите и запустите сервисы, затем проверьте их состояние.

   ```bash
   docker compose -f docker-compose.yml up -d --build
   docker compose -f docker-compose.yml ps
   ```

4. Откройте [http://localhost:5173](http://localhost:5173) и перейдите на вкладку «Приборы», чтобы увидеть карту. Compose запускает PostgreSQL, три Django-сервиса и фронтенд через Nginx. Миграции применяются при запуске контейнеров, при необходимости создаются начальные записи для погрузчика, склада и ячеек.

Если интерфейс недоступен, проверьте логи командой `docker compose -f docker-compose.yml logs --tail=100`. Для остановки выполните `docker compose -f docker-compose.yml down`. Данные PostgreSQL сохраняются в томе `forklift_postgres_data`.

**Подключение AnyLogic и 1С**

- AnyLogic запускается отдельно от Compose. Запустите модель с HTTP-сервером, который отдаёт состояние по `GET /state` и принимает задачи по `POST /order`. По умолчанию контейнеры обращаются к модели по `ANYLOGIC_URL=http://host.docker.internal:8080`. Если модель запущена на другом сервере, укажите его базовый URL в корневом `.env`. Убедитесь, что HTTP-сервер доступен из контейнеров.
- Для синхронизации с 1С задайте `ONEC_API_URL` и при необходимости `ONEC_API_USER`, `ONEC_API_PASSWORD` и `ONEC_WAREHOUSE` в корневом `.env`. Если 1С опубликована на машине, где запущен Docker, используйте в URL `host.docker.internal`.

После изменения настроек повторите команду `docker compose -f docker-compose.yml up -d --build`. AnyLogic и 1С можно подключать по отдельности. Без них интерфейс работает с данными Django и демонстрационным складом.

### Локальный запуск без Docker

Понадобятся Python 3.13, Node.js 20 и запущенный PostgreSQL. Для каждого Django-сервиса задайте `DJANGO_SECRET_KEY` и параметры подключения `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` и `DB_PORT` в окружении или в `.env` рядом с `manage.py`.

#### Backend

Запустите каждый из трёх сервисов (`forklift_dashboard`, `Warehouse`, `Converter`) в отдельном терминале.

```bash
cd forklift_dashboard          # или Warehouse / Converter
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 8000  # 8001 / 8002
```

Папки `migrations/` игнорируются Git. Docker генерирует миграции при сборке
образов и применяет их при запуске контейнеров. Для обновления существующей базы
храните историю миграций вне Git и восстанавливайте её локально из предыдущего
релиза перед запуском `makemigrations` и сборкой образов.

#### Warehouse — переменные окружения

Используйте [Warehouse/.env.example](Warehouse/.env.example) как шаблон для локальных настроек. Для подключения интеграций укажите следующие переменные в `Warehouse/.env`. Если запускаете AnyLogic на другом адресе, задайте тот же `ANYLOGIC_URL` для `forklift_dashboard`.

```env
# Синхронизация ячеек из 1С (опционально)
ONEC_API_URL=
ONEC_API_USER=
ONEC_API_PASSWORD=
ONEC_WAREHOUSE=

# Прокси к AnyLogic (опционально)
ANYLOGIC_URL=http://localhost:8080
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Откройте интерфейс в браузере. [http://localhost:5173](http://localhost:5173)

---

## Структура фронтенда

```
frontend/src/
  api/          — HTTP-клиент и модули API (forklift, tasks, warehouse, converter, anylogic)
  components/
    ForkliftStatus/   — компоненты статуса и хук опроса погрузчика
    Instruments/      — карта, поток AnyLogic, спидометр и сенсоры
    TaskCreation/     — форма создания задачи
    TaskList/         — активные задачи и история
  store/        — Zustand-сторы для UI-состояния
  types/        — TypeScript-типы
```

---

## Интеграции

### 1С — синхронизация ячеек

Запрос `POST /api/warehouse/{id}/sync-from-1c/` получает актуальный список ячеек из 1С и обновляет данные склада.

### AnyLogic — состояние модели и очередь задач

Сервис `Warehouse` читает состояние модели через `GET /state` и передаёт его браузеру через `/api/anylogic/stream`. Для проверки подключения откройте [http://localhost:5173/api/anylogic/state](http://localhost:5173/api/anylogic/state). При доступной модели этот адрес возвращает JSON с ячейками, границами карты и погрузчиками.

При создании задачи Django помещает её в очередь. Планировщик отправляет следующую задачу на `/order`, когда AnyLogic сообщает о свободном погрузчике и в Django нет задачи в работе. Если состояние AnyLogic недоступно, планировщик использует встроенную симуляцию движения по маршруту.

---

## Демонстрация

- [Демонстрация интерфейса 1](https://github.com/user-attachments/assets/adeeb2da-ba28-4fa3-b8a3-af4b649d7304)
- [Демонстрация интерфейса 2](https://github.com/user-attachments/assets/2661d491-2efd-4fce-a3f6-37e51d3c8376)
