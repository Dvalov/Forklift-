from django.db import models
from django.utils import timezone


class Forklift(models.Model):
    STATUS_CHOICES = [
        ('idle', 'Idle'),
        ('moving', 'Moving'),
        ('loading', 'Loading'),
        ('error', 'Error'),
        ('stopped', 'Stopped'),
    ]

    id=models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idle')
    charge_level = models.FloatField(default=0)
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    position_z = models.FloatField(default=0)
    cell_x = models.IntegerField(default=0)
    cell_y = models.IntegerField(default=1)
    cell_z = models.IntegerField(default=0)
    speed = models.FloatField(default=1.0)  # tiles per second
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.id})"

    def update_position(self, x, y, z):
        self.position_x = x
        self.position_y = y
        self.position_z = z
        self.updated_at = timezone.now()
        self.save()

    def emergency_stop(self):
        self.status = 'stopped'
        self.save()
        return self


class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    forklift = models.ForeignKey(Forklift, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')


    origin_x = models.FloatField(default=0)
    origin_y = models.FloatField(default=0)
    origin_z = models.FloatField(default=0)

    dest_x = models.FloatField()
    dest_y = models.FloatField()
    dest_z = models.FloatField()

    dest_cell_x = models.IntegerField(default=1)
    dest_cell_y = models.IntegerField(default=1)
    dest_cell_z = models.IntegerField(default=1)
    path_waypoints = models.JSONField(default=list)  # list of {"x": int, "z": int} dicts

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Task {self.id} - {self.status}"

    def can_modify(self):
        return self.status in ['pending', 'cancelled']

    def cancel(self):
        if self.status == 'pending':
            self.status = 'cancelled'
            self.save()
            return True

    def restore(self):
        if self.status == 'cancelled':
            self.status = 'pending'
            self.save()
            return True


# Create your models here.
