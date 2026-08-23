import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings


class Command(BaseCommand):
    help = "Пересоздать БД: удалить sqlite3, применить миграции, создать погрузчик"

    def add_arguments(self, parser):
        parser.add_argument("--name", type=str, default="Forklift-01", help="Имя погрузчика")

    def handle(self, *args, **options):
        db_path = settings.DATABASES["default"]["NAME"]

        if os.path.exists(db_path):
            os.remove(db_path)
            self.stdout.write(self.style.WARNING(f"Удалена БД: {db_path}"))

        call_command("migrate", verbosity=1)
        call_command("create_forklift", name=options["name"])

        self.stdout.write(self.style.SUCCESS("БД пересоздана успешно."))
