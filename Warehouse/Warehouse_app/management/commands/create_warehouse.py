from django.core.management.base import BaseCommand
from Warehouse_app.models import Warehouse


class Command(BaseCommand):
    help = "Создать склад. Пример: manage.py create_warehouse 'Склад №1'"

    def add_arguments(self, parser):
        parser.add_argument("name", type=str, help="Название склада")

    def handle(self, *args, **options):
        name = options["name"].strip()

        warehouse = Warehouse.objects.create(name=name)

        self.stdout.write(
            self.style.SUCCESS(f"Склад создан: «{warehouse.name}» (id={warehouse.id})")
        )
