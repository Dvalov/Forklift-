from django.apps import AppConfig


class ConverterAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Converter_app'  # Должно точно совпадать с именем папки
    verbose_name = 'Конвертер склада'