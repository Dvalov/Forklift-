from django.core.management.base import BaseCommand
from forklift_dashboard_app.models import Forklift


class Command(BaseCommand):
    help = 'Создать погрузчик. Пример: manage.py create_forklift --name "Forklift-01"'

    def add_arguments(self, parser):
        parser.add_argument("--name", type=str, default="Forklift-01", help="Имя погрузчика")

    def handle(self, *args, **options):
        name = options["name"].strip()

        if Forklift.objects.filter(name=name).exists():
            self.stdout.write(self.style.WARNING(f'Погрузчик «{name}» уже существует — пропускаю.'))
            return

        forklift = Forklift.objects.create(
            name=name,
            status="idle",
            charge_level=100.0,
            position_x=0.0,
            position_y=0.0,
            position_z=0.0,
            cell_x=0,
            cell_y=0,
            cell_z=0,
            speed=0.0,
        )

        self.stdout.write(self.style.SUCCESS(f'Погрузчик создан: «{forklift.name}» (id={forklift.id})'))
