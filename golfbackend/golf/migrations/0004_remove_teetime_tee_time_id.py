# Generated by Django 5.0.6 on 2024-06-07 20:32

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("golf", "0003_alter_golfcourse_golf_club"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="teetime",
            name="tee_time_id",
        ),
    ]
