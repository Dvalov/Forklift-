from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('forklift_dashboard_app', '0004_forklift_charge_level'),
    ]
    operations = [
        migrations.AddField(
            model_name='task',
            name='path_waypoints',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='forklift',
            name='speed',
            field=models.FloatField(default=1.0),
        ),
    ]
