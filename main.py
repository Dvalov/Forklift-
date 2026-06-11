from forklift_dashboard_app.models import Forklift

# Посмотрим всех погрузчиков
for forklift in Forklift.objects.all():
    print(f"ID: {forklift.id}, Name: {forklift.name}, Status: {forklift.status}")
