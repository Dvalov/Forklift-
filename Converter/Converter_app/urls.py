from django.urls import path
from . import views

app_name = 'Converter_app'

urlpatterns = [
    # Основные endpoints
    path('api/converter/<int:warehouse_id>/cells/convert/',
         views.convert_cell_address,
         name='convert_cell'),

    path('api/converter/<int:warehouse_id>/cells/get_path/',
         views.get_cell_path,
         name='get_cell_path'),

    # Управление размерами склада
    path('api/converter/<int:warehouse_id>/size/',
         views.manage_warehouse_size,
         name='manage_size'),

    # Список всех складов
    path('api/converter/warehouses/',
         views.list_warehouses,
         name='list_warehouses'),
]

