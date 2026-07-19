from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from Warehouse_app.models import Warehouse, Cell


class Command(BaseCommand):
    help = (
        "Очистить все ячейки склада и создать заново с проходами.\n"
        "Стеллажи — нечётные x (1, 3, 5, ...), проходы — чётные x (0, 2, 4, ...).\n"
        "Пример: manage.py reset_cells 1 --cols 5 --shelves 3 --rows 3"
    )

    def add_arguments(self, parser):
        parser.add_argument("warehouse_id", type=int, help="ID склада")
        parser.add_argument("--cols", type=int, default=5,
                            help="Количество колонн стеллажей (x=1,3,...; default: 5)")
        parser.add_argument("--shelves", type=int, default=3,
                            help="Ярусов в высоту (y=1..N; default: 3)")
        parser.add_argument("--rows", type=int, default=3,
                            help="Количество рядов вглубь (z=1..N; default: 3)")

    def handle(self, *args, **options):
        wid = options["warehouse_id"]
        cols = options["cols"]
        shelves = options["shelves"]
        rows = options["rows"]

        try:
            warehouse = Warehouse.objects.get(pk=wid)
        except Warehouse.DoesNotExist:
            raise CommandError(f"Склад с id={wid} не найден")

        # x=1,3,5,...  (нечётные — стеллажи, чётные — проходы)
        x_values = [2 * i - 1 for i in range(1, cols + 1)]

        with transaction.atomic():
            deleted, _ = warehouse.cells.all().delete()
            self.stdout.write(self.style.WARNING(f"Удалено: {deleted} ячеек"))

            cells = [
                Cell(warehouse=warehouse, x=x, y=y, z=z, available=True)
                for x in x_values
                for y in range(1, shelves + 1)
                for z in range(1, rows + 1)
            ]
            Cell.objects.bulk_create(cells)

        self.stdout.write(self.style.SUCCESS(
            f"Создано {len(cells)} ячеек для склада «{warehouse.name}»\n"
            f"  Стеллажи x: {x_values}\n"
            f"  Проходы  x: {[x - 1 for x in x_values] + [x_values[-1] + 1]}\n"
            f"  Ярусы    y: 1..{shelves}\n"
            f"  Ряды     z: 1..{rows}"
        ))
