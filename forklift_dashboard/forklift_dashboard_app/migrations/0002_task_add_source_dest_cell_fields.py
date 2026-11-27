from django.db import migrations, models

from ._operations import AddFieldIfMissing


class Migration(migrations.Migration):

    dependencies = [
        ('forklift_dashboard_app', '0001_initial'),
    ]

    operations = [
        AddFieldIfMissing(
            model_name='task',
            name='source_cell_x',
            field=models.IntegerField(default=0),
        ),
        AddFieldIfMissing(
            model_name='task',
            name='source_cell_y',
            field=models.IntegerField(default=0),
        ),
        AddFieldIfMissing(
            model_name='task',
            name='source_cell_z',
            field=models.IntegerField(default=0),
        ),
        AddFieldIfMissing(
            model_name='task',
            name='source_cell_name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        AddFieldIfMissing(
            model_name='task',
            name='dest_cell_name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
