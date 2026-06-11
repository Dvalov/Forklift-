from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Подключаем URL-ы приложения Converter_app
    path('', include('Converter_app.urls')),
]
