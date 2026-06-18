from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forklift_dashboard_app', '0003_rename_task_forklift_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='forklift',
            name='charge_level',
            field=models.FloatField(default=0),
        ),
    ]
