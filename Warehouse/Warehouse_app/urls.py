from django.urls import path
from .views import CellListView, CellDetailView

urlpatterns = [
    path('api/warehouse/<int:id>/cells/', CellListView.as_view(), name='cell-list'),
    path('api/warehouse/<int:id>/cell/', CellDetailView.as_view(), name='cell-detail'),
]