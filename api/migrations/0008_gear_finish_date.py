# Generated by Django 4.2.3 on 2023-10-30 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_alter_gear_level_alter_gear_token_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='gear',
            name='finish_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]