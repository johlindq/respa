# Generated by Django 2.2.11 on 2020-12-01 07:22

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('resources', '0123_auto_20201103_1136'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OutlookCalendarLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.TextField(verbose_name='Token')),
                ('reservation_calendar_id', models.TextField(verbose_name='Outlook calendar id')),
                ('availability_calendar_id', models.TextField(verbose_name='Availability calendar id')),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='resources.Resource', verbose_name='Resource')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
        ),
        migrations.CreateModel(
            name='OutlookTokenRequestData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.TextField(unique=True)),
                ('created_at', models.DateTimeField()),
                ('return_to', models.URLField()),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='resources.Resource', verbose_name='Resource')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
        ),
        migrations.CreateModel(
            name='OutlookCalendarReservation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exchange_id', models.TextField(unique=True, verbose_name='Exchange ID')),
                ('exchange_change_key', models.TextField(verbose_name='Exchange Change Key')),
                ('respa_change_key', models.TextField(verbose_name='Respa Change Key')),
                ('calendar_link', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='respa_o365.OutlookCalendarLink', verbose_name='Calendar Link')),
                ('reservation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='resources.Reservation', verbose_name='Reservation')),
            ],
        ),
    ]
