import os
from django.apps import AppConfig


class ForkliftDashboardAppConfig(AppConfig):
    name = "forklift_dashboard_app"

    def ready(self):
        import sys
        # RUN_MAIN=true in child process with auto-reloader; not set with --noreload
        if os.environ.get('RUN_MAIN') == 'true' or '--noreload' in sys.argv:
            from .scheduler import start_scheduler
            start_scheduler()
