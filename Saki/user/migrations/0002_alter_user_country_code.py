# Generated by Django 4.2.7 on 2023-12-16 20:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='country_code',
            field=models.CharField(max_length=10),
        ),
    ]