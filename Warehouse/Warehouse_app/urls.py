from django.urls import path
from .views import CellListView, CellDetailView, SyncFromOneCView

urlpatterns = [
    path('api/warehouse/<int:id>/cells/', CellListView.as_view(), name='cell-list'),
    path('api/warehouse/<int:id>/cell/', CellDetailView.as_view(), name='cell-detail'),
    path('api/warehouse/<int:warehouse_id>/sync-from-1c/', SyncFromOneCView.as_view(), name='sync-from-1c'),
]