"""
Migration: Remove car vehicles and type field
將系統改為純機車模式：刪除所有汽車資料並移除 type 字段
"""
from django.db import migrations


def delete_car_vehicles(apps, schema_editor):
    """刪除所有 type='car' 的車輛資料"""
    Vehicle = apps.get_model('motry', 'Vehicle')
    count = Vehicle.objects.filter(type__iexact='car').count()
    Vehicle.objects.filter(type__iexact='car').delete()
    if count > 0:
        print(f"\n  已刪除 {count} 筆汽車資料")


def restore_car_vehicles(apps, schema_editor):
    """反向遷移：無法恢復已刪除的資料，僅作為佔位符"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('motry', '0005_comment_is_deleted_post_is_deleted_and_more'),
    ]

    operations = [
        # 1. 先刪除所有汽車資料
        migrations.RunPython(delete_car_vehicles, restore_car_vehicles),
        # 2. 移除 type 字段
        migrations.RemoveField(
            model_name='vehicle',
            name='type',
        ),
    ]
