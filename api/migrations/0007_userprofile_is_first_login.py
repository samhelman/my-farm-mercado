# Generated by Django 3.1.4 on 2021-01-21 13:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_shoppinglist_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='is_first_login',
            field=models.BooleanField(default=True),
        ),
    ]
