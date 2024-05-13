# Generated by Django 5.0.6 on 2024-05-13 06:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0011_merge_0010_course_course_success_video_0010_rating"),
    ]

    operations = [
        migrations.AddField(
            model_name="testsubmission",
            name="selected_answers",
            field=models.ManyToManyField(
                related_name="user_checked_answers", to="courses.answer"
            ),
        ),
        migrations.AlterField(
            model_name="course",
            name="course_picture",
            field=models.ImageField(
                default="static/core/images/course-default-bg.png",
                upload_to="course_pictures/",
            ),
        ),
    ]
