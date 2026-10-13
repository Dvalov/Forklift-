# Forklift Dashboard

Промышленная веб-панель для операторов складских погрузчиков. Оператор видит состояние погрузчика в реальном времени и создаёт задачи выбором ячейки склада — всё в одном экране.

<img width="1919" height="958" alt="панель приборов" src="https://github.com/user-attachments/assets/3e6de0e2-13d8-474d-9340-6707d3b3e2dc" />
<img width="1919" height="952" alt="панель задач" src="https://github.com/user-attachments/assets/ebaefe81-68ce-4235-8da2-771c48a09dd8" />

---

## Стек

| Слой | Технологии |
|---|---|
| Frontend | React 19, TypeScript, Vite, TanStack Query v5, Zustand v5, Tailwind CSS |
| Backend | Django 6, Django REST Framework, django-cors-headers |
| Интеграции | 1C (синхронизация ячеек), AnyLogic (позиция погрузчика) - аналог реального склада и погрузчика |

---

## Архитектура

Три независимых Django-сервиса и React-фронтенд:

```
forklift_dashboard/   → :8000  — погрузчики, задачи
Warehouse/            → :8001  — ячейки склада
Converter/            → :8002  — адрес ячейки → координаты XYZ
frontend/             → :5173  — React UI (Vite dev server)
```

Фронтенд обращается ко всем трём сервисам через `src/api/client.ts`. Данные обновляются поллингом каждые 3–5 с.

---

## Функциональность

**Вкладка «Задачи»**
- Форма создания задачи с выбором ячейки склада
- Кнопка для синхронизации ячеек из 1с
- Список активных задач погрузчика
- История завершённых задач

**Вкладка «Приборы»**
- Карта склада с позицией и маршрутом погрузчика
- Спидометр, уровень заряда батареи
- Данные гидравлики и сенсоров (дальномеры, температуры, нагрузка)
- AI-рекомендации (скорость, заряд, предупреждения)
- Статус связи, режим работы, диагностика

---

## Запуск

### Требования

- Python 3.11+
- Node.js 20+

### Backend

Для каждого из трёх сервисов (`forklift_dashboard`, `Warehouse`, `Converter`):

```bash
cd forklift_dashboard          # или Warehouse / Converter
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000  # 8001 / 8002
```

### Warehouse — переменные окружения

Скопируйте `Warehouse/.env.example` → `Warehouse/.env` и заполните:

```env
DJANGO_SECRET_KEY=your-secret-key

# Синхронизация ячеек из 1C (опционально)
ONEC_API_URL=
ONEC_API_USER=
ONEC_API_PASSWORD=
ONEC_WAREHOUSE=

# Прокси к AnyLogic (опционально)
ANYLOGIC_URL=http://localhost:8080
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Открыть: [http://localhost:5173](http://localhost:5173)

---

## Структура фронтенда

```
frontend/src/
  api/          — client.ts + модули по сервисам (forklift, tasks, warehouse, converter)
  components/
    ForkliftStatus/   — статус бар вверху
    Instruments/      — вкладка «Приборы» (карта, спидометр, сенсоры)
    TaskCreation/     — форма создания задачи
    TaskList/         — активные задачи и история
  hooks/        — React-хуки для поллинга данных
  store/        — Zustand-сторы для UI-состояния
  types/        — TypeScript-типы
```

---

## Интеграции

### 1C — синхронизация ячеек

`POST /api/warehouse/{id}/sync-from-1c/` — тянет актуальный список ячеек из 1C и обновляет склад.

### AnyLogic — позиция погрузчика

Сервис `Warehouse` проксирует запросы к встроенному HTTP-серверу AnyLogic-модели для получения координат погрузчика в реальном времени.

---

## Состояние проекта

### Готово
- Все три backend-сервиса запускаются и отдают данные
- Создание и отслеживание задач погрузчика
- Синхронизация ячеек склада из 1C
- Вкладка «Приборы»: карта, спидометр, сенсоры, AI-рекомендации
- Backend-эндпоинт `POST /api/warehouse/{id}/anylogic/task/` — отправляет задачу погрузчику в AnyLogic-модель

https://github.com/user-attachments/assets/adeeb2da-ba28-4fa3-b8a3-af4b649d7304

https://github.com/user-attachments/assets/2661d491-2efd-4fce-a3f6-37e51d3c8376



### В работе / не реализовано

**WarehouseMap из AnyLogic**
- Карта на вкладке «Приборы» показывает демо-данные; нужно перейти на реальные пиксельные координаты из AnyLogic-модели
- Предстоит: `useAnyLogicQuery` hook (поллинг `/api/anylogic/state`) + SVG-рендеринг ячеек по `centerX/centerY` из симуляции

**Task Creation → AnyLogic Order**
- Фронтенд не отправляет заказ в AnyLogic при создании задачи
- Предстоит: fire-and-forget `POST /api/anylogic/order` после успешного `POST /api/tasks/`; если AnyLogic недоступен — задача в Django создаётся без ошибки

---
