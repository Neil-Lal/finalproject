# Generated by Django 2.2.7 on 2019-12-01 02:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reports',
            name='required_fields',
        ),
        migrations.AddField(
            model_name='reports',
            name='required_field',
            field=models.TextField(default='test'),
            preserve_default=False,
        ),
    ]
