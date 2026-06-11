from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ForkliftViewSet, TaskViewSet

router = DefaultRouter()
router.register(r'forklifts', ForkliftViewSet, basename='forklift')
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('api/', include(router.urls)),
    
]