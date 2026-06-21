from Warehouse_app.models import Warehouse, Cell

w, _ = Warehouse.objects.get_or_create(id=1, defaults={'name': 'Main Warehouse'})
print(f"Склад: {w.name} (id={w.id})")

created_count = 0
for x in range(1, 4):
    for y in range(1, 4):
        for z in range(1, 3):
            _, created = Cell.objects.get_or_create(
                warehouse=w, x=x, y=y, z=z,
                defaults={'available': True}
            )
            if created:
                created_count += 1

total = Cell.objects.filter(warehouse=w).count()
print(f"Создано новых: {created_count}, всего ячеек: {total}")
