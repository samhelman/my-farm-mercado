# Generated by Django 3.1.4 on 2021-01-26 22:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_auto_20210125_2340'),
    ]

    operations = [
        migrations.AddField(
            model_name='shoppinglistitem',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True),
        ),
    ]
