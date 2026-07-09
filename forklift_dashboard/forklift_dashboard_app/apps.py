import os
from django.apps import AppConfig


class ForkliftDashboardAppConfig(AppConfig):
    name = "forklift_dashboard_app"

    def ready(self):
        if os.environ.get('RUN_MAIN') == 'true':
            from .scheduler import start_scheduler
            start_scheduler()
