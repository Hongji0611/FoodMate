# Generated by Django 3.1 on 2020-08-22 21:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photo', '0004_auto_20200822_2109'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo',
            name='deal',
            field=models.CharField(choices=[('모집 중', '모집 중'), ('모집 완료', '모집 완료')], default='Y', max_length=50),
        ),
    ]
