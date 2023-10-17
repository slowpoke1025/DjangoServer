# Generated by Django 4.2.3 on 2023-08-30 23:15

import api.utils.ethereum
from django.db import migrations, models
import siwe.siwe


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('address', models.CharField(default=api.utils.ethereum.generate_random_ethereum_address, max_length=42, unique=True)),
                ('username', models.CharField(max_length=255, unique=True)),
                ('weight', models.PositiveIntegerField(blank=True, null=True)),
                ('height', models.PositiveIntegerField(blank=True, null=True)),
                ('gender', models.CharField(blank=True, choices=[('Male', 'MALE'), ('Female', 'FEMALE'), ('Other', 'OTHER')], max_length=6, null=True)),
                ('birth', models.DateField(blank=True, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('email', models.EmailField(blank=True, max_length=255)),
                ('nonce', models.CharField(default=siwe.siwe.generate_nonce, max_length=36)),
                ('is_active', models.BooleanField(default=True)),
                ('is_superuser', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'user',
                'managed': True,
            },
        ),
    ]