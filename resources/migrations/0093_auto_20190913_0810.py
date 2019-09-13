# Generated by Django 2.1.12 on 2019-09-13 05:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0092_auto_20190912_1419'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='state',
            field=models.CharField(choices=[('created', 'created'), ('cancelled', 'cancelled'), ('confirmed', 'confirmed'), ('denied', 'denied'), ('requested', 'requested')], default='created', max_length=16, verbose_name='State'),
        ),
    ]
