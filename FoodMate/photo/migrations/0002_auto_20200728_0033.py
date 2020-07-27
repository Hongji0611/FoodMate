# Generated by Django 3.0.8 on 2020-07-27 15:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('photo', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo',
            name='category',
            field=models.CharField(choices=[('fruit', '과일'), ('vegetable', '채소'), ('meat', '정육'), ('dairy', '계란/유제품'), ('fish', '수산/건어물'), ('main_food', '쌀/김치/반찬'), ('bakery', '베이커리'), ('dessert', '디저트/음료'), ('health_food', '가공/건강식품'), ('household', '생활용품')], max_length=50),
        ),
        migrations.AlterField(
            model_name='photo',
            name='count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='photo',
            name='money',
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(default='')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('parentComment', models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='photo.Comment')),
                ('photo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='photo.Photo')),
                ('username', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='comments', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
