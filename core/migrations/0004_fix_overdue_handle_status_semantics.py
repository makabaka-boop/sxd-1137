from django.db import migrations, models
from django.utils import timezone


def clear_non_overdue_pending_status(apps, schema_editor):
    PatrolRecord = apps.get_model('core', 'PatrolRecord')
    today = timezone.now().date()
    PatrolRecord.objects.filter(overdue_handle_status='pending').exclude(
        status='approved',
        is_returned=False,
        due_date__lt=today
    ).update(overdue_handle_status=None)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_patrolrecord_overdue_handle_remark_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patrolrecord',
            name='overdue_handle_status',
            field=models.CharField(blank=True, choices=[('pending', '待处理'), ('handled', '已处理')], max_length=20, null=True, verbose_name='逾期处理状态'),
        ),
        migrations.RunPython(clear_non_overdue_pending_status, migrations.RunPython.noop),
    ]
