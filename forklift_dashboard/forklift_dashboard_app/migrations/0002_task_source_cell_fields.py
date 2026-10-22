from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forklift_dashboard_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='source_cell_x',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='task',
            name='source_cell_y',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='task',
            name='source_cell_z',
            field=models.IntegerField(default=0),
        ),
    ]
