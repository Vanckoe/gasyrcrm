# Generated by Django 5.0.4 on 2024-05-20 05:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0002_shift_shifttime'),
        ('subjects', '0007_remove_lesson_crm2_schedule'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Schedule',
        ),
    ]
