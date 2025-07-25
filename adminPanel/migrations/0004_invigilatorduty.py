# Generated by Django 5.2 on 2025-04-27 20:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminPanel', '0003_exam_teacher_venue'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvigilatorDuty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('assigned', 'Assigned'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')], default='assigned', max_length=20)),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='adminPanel.exam')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='adminPanel.teacher')),
                ('venue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='adminPanel.venue')),
            ],
            options={
                'unique_together': {('teacher', 'exam')},
            },
        ),
    ]
