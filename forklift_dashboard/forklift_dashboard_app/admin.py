import logging

from django.contrib import admin
from .models import Forklift, Task

logger = logging.getLogger(__name__)


# Регистрация модели Forklift
@admin.register(Forklift)
class ForkliftAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'status', 'position_x', 'position_y', 'position_z', 'updated_at')
    list_filter = ('status',)
    search_fields = ('name', 'id')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at')


# Регистрация модели Task
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'forklift_id', 'status', 'dest_x', 'dest_y', 'dest_z', 'created_at')
    list_filter = ('status',)
    search_fields = ('id',)
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            logger.info("Task %s created: forklift=%s status=%s source=admin",
                        obj.pk, obj.forklift_id, obj.status)
        elif 'status' in form.changed_data:
            logger.info("Task %s status: %s -> %s (forklift=%s source=admin)",
                        obj.pk, form.initial.get('status'), obj.status, obj.forklift_id)

from django.contrib import admin

# Register your models here.
