# Generated by Django 5.0.6 on 2024-07-06 20:28

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("golf", "0008_alter_golfcourse_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="golfclub",
            name="disabled",
            field=models.BooleanField(default=False),
        ),
    ]
