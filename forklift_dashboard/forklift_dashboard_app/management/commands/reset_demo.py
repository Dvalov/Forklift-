from django.core.management.base import BaseCommand
from forklift_dashboard_app.models import Forklift, Task


class Command(BaseCommand):
    help = "Сбросить демо: удалить все задачи, погрузчик вернуть в (0,0), заряд 100%%"

    def handle(self, *args, **options):
        deleted, _ = Task.objects.all().delete()
        self.stdout.write(self.style.WARNING(f"Удалено задач: {deleted}"))

        updated = Forklift.objects.update(
            position_x=0.0,
            position_y=0.0,
            position_z=0.0,
            speed=0.0,
            charge_level=100.0,
            status="idle",
        )
        self.stdout.write(self.style.SUCCESS(f"Сброшено погрузчиков: {updated}"))
