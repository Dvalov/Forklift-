from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from Warehouse_app.models import Warehouse, Cell


class Command(BaseCommand):
    help = "Очистить ячейки склада и создать заново. Пример: manage.py seed_cells 1 --x 5 --y 3 --z 2"

    def add_arguments(self, parser):
        parser.add_argument("warehouse_id", type=int, help="ID склада")
        parser.add_argument("--x", type=int, default=5, help="Количество ячеек по оси X (default: 5)")
        parser.add_argument("--y", type=int, default=5, help="Количество ячеек по оси Y (default: 5)")
        parser.add_argument("--z", type=int, default=3, help="Количество ячеек по оси Z (default: 3)")

    def handle(self, *args, **options):
        warehouse_id = options["warehouse_id"]
        x_count = options["x"]
        y_count = options["y"]
        z_count = options["z"]

        try:
            warehouse = Warehouse.objects.get(pk=warehouse_id)
        except Warehouse.DoesNotExist:
            raise CommandError(f"Склад с id={warehouse_id} не найден")

        total = x_count * y_count * z_count

        with transaction.atomic():
            deleted, _ = warehouse.cells.all().delete()
            self.stdout.write(self.style.WARNING(f"Удалено: {deleted} ячеек"))

            cells = [
                Cell(warehouse=warehouse, x=x, y=y, z=z, available=True)
                for x in range(1, x_count + 1)
                for y in range(1, y_count + 1)
                for z in range(1, z_count + 1)
            ]
            Cell.objects.bulk_create(cells)

        self.stdout.write(self.style.SUCCESS(
            f"Создано {total} ячеек для склада «{warehouse.name}»\n"
            f"  X: 1..{x_count}\n"
            f"  Y: 1..{y_count}\n"
            f"  Z: 1..{z_count}"
        ))
