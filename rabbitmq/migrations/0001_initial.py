# Generated by Django 3.1.1 on 2020-09-11 14:52

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CachedCommission',
            fields=[
                ('commission_id', models.IntegerField(primary_key=True, serialize=False)),
                ('title', models.TextField(max_length=32768)),
            ],
        ),
    ]
