from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forklift_dashboard_app', '0002_task_source_cell_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='source_cell_name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='task',
            name='dest_cell_name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
