# Warehouse/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Warehouse_app.urls')),  # ИСПРАВЛЕНО: warehouse -> Warehouse_app
]