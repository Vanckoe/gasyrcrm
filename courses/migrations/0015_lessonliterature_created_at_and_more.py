# Generated by Django 5.0.4 on 2024-08-22 09:34

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0014_course_published'),
    ]

    operations = [
        migrations.AddField(
            model_name='lessonliterature',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='lessonliterature',
            name='file',
            field=models.FileField(upload_to='literature_files/'),
        ),
        migrations.AlterField(
            model_name='lessonliterature',
            name='literature_name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='lessonliterature',
            name='literature_type',
            field=models.CharField(choices=[('Book', 'Book'), ('Video', 'Video'), ('Text', 'Text'), ('Audio', 'Audio'), ('Generic', 'Generic')], default='Generic', max_length=20),
        ),
        migrations.CreateModel(
            name='Homework',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('homework_name', models.CharField(max_length=100)),
                ('file', models.FileField(upload_to='homework_files/')),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='homeworks', to='courses.lesson')),
            ],
        ),
    ]
