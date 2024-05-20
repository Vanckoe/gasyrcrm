# Generated by Django 5.0.4 on 2024-05-20 05:27

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0008_remove_lesson_crm2_shift_lesson_crm2_time_slot'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='VolunteerChannel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('image', models.ImageField(blank=True, null=True, upload_to='volunteer_channel_images/')),
                ('users', models.ManyToManyField(limit_choices_to={'role': 'Mentor'}, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
