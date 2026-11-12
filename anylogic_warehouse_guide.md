# Симуляция склада в AnyLogic — руководство

## Структура модели

```
Main
├── Agent: Forklift    (погрузчик)
├── Agent: Order       (задание/заказ)
└── Agent: StorageCell (ячейка склада)
```

---

## Шаг 1 — Создай агентов

### Agent: Forklift

Параметры:
| Параметр | Тип | Значение |
|---|---|---|
| `speed` | double | 5.0 (м/с) |
| `capacity` | int | 1 |
| `chargeLevel` | double | 100.0 |

Переменные:
- `currentOrder` — ссылка на Order (тип: Agent)
- `isBusy` — boolean

### Agent: Order

Параметры:
| Параметр | Тип |
|---|---|
| `sourceCellId` | int |
| `destCellId` | int |
| `priority` | int |
| `createdAt` | double |

### Agent: StorageCell

Параметры:
| Параметр | Тип |
|---|---|
| `cellId` | int |
| `row` | int |
| `col` | int |
| `occupied` | boolean |

---

## Шаг 2 — Карта склада в Main

1. **Space Markup → Rectangular Node** — зона склада целиком
2. **Space Markup → Rectangular Node** × N — зоны стеллажей
3. **Space Markup → Path** — коридоры движения погрузчиков
4. **Space Markup → Point Node** — точки приёмки (Input) и отгрузки (Output)

Схема расположения:
```
[INPUT]  [----corridor----]  [OUTPUT]
         | R1 | R2 | R3 |
         | R4 | R5 | R6 |
         [----corridor----]
```

---

## Шаг 3 — Statechart для Forklift

```
State: Idle
  → on(new order assigned) → GoToSource

State: GoToSource
  → moveTo(sourceCell)
  → on(arrived) → PickUp

State: PickUp
  → delay(2 sec)
  → GoToDest

State: GoToDest
  → moveTo(destCell)
  → on(arrived) → PutDown

State: PutDown
  → delay(2 sec)
  → Complete

State: Complete
  → sourceCell.occupied = false
  → destCell.occupied = true
  → order.complete()
  → Idle
```

В состояниях GoToSource / GoToDest используй transition типа **Condition**, условие: `isMoving() == false`.

Action на входе в GoToSource:
```java
StorageCell src = storageCells.get(currentOrder.sourceCellId);
moveTo(src);
```

---

## Шаг 4 — Генерация заказов в Main

Используй блок **Event** (тип: Rate или Timeout):

```java
// Event: generateOrder, timeout: exponential(5) минут
Order order = add_orders(new Order());
order.sourceCellId = (int)(uniform(0, storageCells.size()));
order.destCellId   = (int)(uniform(0, storageCells.size()));
order.createdAt    = time();

// Найти свободный погрузчик
for (Forklift f : forklifts) {
    if (!f.isBusy) {
        f.currentOrder = order;
        f.isBusy = true;
        f.statechart.fireEvent(new NewOrder());
        break;
    }
}
```

---

## Шаг 5 — Статистика

Добавь в Main:
- `DataSet: orderCompletionTime`
- `HistogramData: utilizationHist`
- **TimePlot** — загруженность погрузчиков во времени
- **BarChart** — кол-во выполненных/в очереди заказов

В конце каждого заказа:
```java
orderCompletionTime.add(time() - order.createdAt);
```

---

## Шаг 6 — 3D визуализация (опционально)

- Назначь погрузчику **3D Object** → `Forklift.obj` из библиотеки AnyLogic
- Для стеллажей используй **Box 3D** из палитры

---

## Как добавить параметр агенту

### Способ 1 — Через палитру

1. Открой тип агента двойным кликом
2. Палитра слева → раздел **Agent** → **Parameter**
3. Перетащи **Parameter** на холст агента
4. В панели свойств задай: **Name**, **Type**, **Default value**

### Способ 2 — Через Properties

1. Кликни на пустое место холста агента
2. Панель свойств → вкладка **Parameters**
3. Нажми **+** → задай имя и тип

### Использование параметра в коде

```java
// Внутри агента
moveTo(speed);

// Из Main или другого агента
Forklift f = forklifts.get(0);
f.speed = 7.5;
```

### Parameter vs Variable

| | Parameter | Variable |
|---|---|---|
| Задаётся при создании агента | Да | Нет |
| Можно менять во время симуляции | Да | Да |
| Используется для | настройки агента | текущего состояния |

**Правило:** настройки агента (скорость, ёмкость) → `Parameter`. Текущее состояние (заряд, статус) → `Variable`.

---

## Main — корневой агент

Main — это тоже агент, корневой (root agent), создаётся автоматически.

### Иерархия

```
Main  (корневой агент)
├── forklifts: List<Forklift>
├── orders: List<Order>
└── storageCells: List<StorageCell>
```

### Глобальные параметры в Main

```
numForklifts   int     = 3
orderRate      double  = 0.2   // заказов в минуту
warehouseSize  int     = 20    // кол-во ячеек
```

---

## Восстановление удалённого Main

### Шаг 1 — Создай новый тип агента Main

1. Дерево проекта → правая кнопка на проект → **New → Agent**
2. **Name:** `Main` (с большой буквы)
3. Нажми **Finish**

### Шаг 2 — Назначь Main корневым агентом

1. В дереве проекта найди **Simulation** (иконка колбы)
2. Двойной клик → свойства эксперимента
3. Поле **Top-level agent** → выбери `Main`

### Шаг 3 — Проверь

Нажми **Run (▶)** — модель должна запуститься без ошибок.

### Если Simulation тоже удалён

Правая кнопка на проект → **New → Simulation Experiment** → поле **Top-level agent** → `Main`.

---

## Минимальная схема для старта

| Что создать | Компонент AnyLogic |
|---|---|
| Карта | Space Markup |
| Погрузчик | Agent + Statechart + moveTo() |
| Заказ | Agent (данные) |
| Генерация заказов | Event (Rate) |
| Очередь заказов | Collection (LinkedList) в Main |
| Статистика | DataSet + TimePlot |
