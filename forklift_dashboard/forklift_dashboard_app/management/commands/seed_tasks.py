import random
from django.core.management.base import BaseCommand
from forklift_dashboard_app.models import Forklift, Task

FORKLIFT_NAME = "Forklift-01"

SAMPLE_TASKS = [
    {
        "status": "pending",
        "origin_x": 0.0, "origin_y": 0.0, "origin_z": 0.0,
        "dest_x": 10.0,  "dest_y": 0.0,  "dest_z": 5.0,
        "dest_cell_x": 1, "dest_cell_y": 1, "dest_cell_z": 1,
    },
    {
        "status": "pending",
        "origin_x": 0.0, "origin_y": 0.0, "origin_z": 0.0,
        "dest_x": 20.0,  "dest_y": 0.0,  "dest_z": 10.0,
        "dest_cell_x": 2, "dest_cell_y": 1, "dest_cell_z": 2,
    },
    {
        "status": "in_progress",
        "origin_x": 0.0, "origin_y": 0.0, "origin_z": 0.0,
        "dest_x": 30.0,  "dest_y": 0.0,  "dest_z": 15.0,
        "dest_cell_x": 3, "dest_cell_y": 1, "dest_cell_z": 3,
    },
    {
        "status": "completed",
        "origin_x": 0.0, "origin_y": 0.0, "origin_z": 0.0,
        "dest_x": 40.0,  "dest_y": 0.0,  "dest_z": 20.0,
        "dest_cell_x": 4, "dest_cell_y": 2, "dest_cell_z": 1,
    },
    {
        "status": "failed",
        "origin_x": 0.0, "origin_y": 0.0, "origin_z": 0.0,
        "dest_x": 50.0,  "dest_y": 0.0,  "dest_z": 25.0,
        "dest_cell_x": 5, "dest_cell_y": 2, "dest_cell_z": 2,
    },
    {
        "status": "cancelled",
        "origin_x": 0.0, "origin_y": 0.0, "origin_z": 0.0,
        "dest_x": 15.0,  "dest_y": 0.0,  "dest_z": 30.0,
        "dest_cell_x": 2, "dest_cell_y": 3, "dest_cell_z": 1,
    },
]


class Command(BaseCommand):
    help = f'Seed tasks for "{FORKLIFT_NAME}"'

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing tasks before seeding",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=0,
            help="Generate N random extra tasks in addition to the fixed samples",
        )

    def handle(self, *args, **options):
        try:
            forklift = Forklift.objects.get(name=FORKLIFT_NAME)
        except Forklift.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Forklift "{FORKLIFT_NAME}" not found in DB.'))
            return

        self.stdout.write(f"  Using forklift: {forklift}")

        if options["clear"]:
            deleted, _ = Task.objects.filter(forklift=forklift).delete()
            self.stdout.write(self.style.WARNING(f"  Cleared {deleted} task(s)."))

        created_count = 0

        for data in SAMPLE_TASKS:
            task = Task.objects.create(forklift=forklift, **data)
            created_count += 1
            self.stdout.write(
                f"  Created task #{task.id}: status={task.status}, "
                f"dest_cell=({task.dest_cell_x},{task.dest_cell_y},{task.dest_cell_z})"
            )

        statuses = [s for s, _ in Task.STATUS_CHOICES]
        for _ in range(options["count"]):
            task = Task.objects.create(
                forklift=forklift,
                status=random.choice(statuses),
                origin_x=round(random.uniform(0, 50), 2),
                origin_y=0.0,
                origin_z=round(random.uniform(0, 50), 2),
                dest_x=round(random.uniform(0, 100), 2),
                dest_y=0.0,
                dest_z=round(random.uniform(0, 100), 2),
                dest_cell_x=random.randint(1, 10),
                dest_cell_y=random.randint(1, 5),
                dest_cell_z=random.randint(1, 3),
            )
            created_count += 1
            self.stdout.write(f"  Created random task #{task.id}: status={task.status}")

        self.stdout.write(self.style.SUCCESS(f"\nDone. Created {created_count} task(s)."))
