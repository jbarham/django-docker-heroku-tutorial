# Generated by Django 2.2.10 on 2020-02-22 00:21

import django.core.management.utils
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Secret',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('key', models.CharField(default=django.core.management.utils.get_random_secret_key, max_length=50)),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
    ]
