# Generated by Django 2.2.7 on 2019-12-04 23:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
        ('app', '0004_announcements'),
    ]

    operations = [
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('time', models.CharField(choices=[('ONUPLOAD', 'Upload')], default='ONUPLOAD', max_length=50)),
                ('permission_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_perm', to='auth.Group')),
            ],
        ),
        migrations.CreateModel(
            name='ExportReports',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('report_data', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_data', to='app.Reports')),
            ],
        ),
    ]
