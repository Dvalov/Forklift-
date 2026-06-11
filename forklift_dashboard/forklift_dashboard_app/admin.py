from django.contrib import admin
from .models import Forklift, Task


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


from django.contrib import admin

# Register your models here.
