from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import EquipmentType, StorageLocation, BorrowRule, Equipment
from datetime import date


class Command(BaseCommand):
    help = '初始化测试数据'

    def handle(self, *args, **options):
        self.stdout.write('开始初始化数据...')

        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'a****@***********', 'admin123')
            self.stdout.write(self.style.SUCCESS('创建管理员用户: admin / admin123'))

        if not User.objects.filter(username='employee_a').exists():
            User.objects.create_user('employee_a', 'e***********@***********', 'emp123456')
            self.stdout.write(self.style.SUCCESS('创建员工A用户: employee_a / emp123456'))

        if not User.objects.filter(username='employee_b').exists():
            User.objects.create_user('employee_b', 'e***********@***********', 'emp123456')
            self.stdout.write(self.style.SUCCESS('创建员工B用户: employee_b / emp123456'))

        equipment_types = [
            {'name': '笔记本电脑', 'code': 'LAPTOP'},
            {'name': '投影仪', 'code': 'PROJECTOR'},
            {'name': '摄像机', 'code': 'CAMERA'},
            {'name': '麦克风', 'code': 'MIC'},
            {'name': '平板电脑', 'code': 'TABLET'},
        ]
        for et in equipment_types:
            EquipmentType.objects.get_or_create(**et)
        self.stdout.write(self.style.SUCCESS('初始化器材类型数据'))

        locations = [
            {'name': 'A区1号柜', 'code': 'A01', 'area': 'A区'},
            {'name': 'A区2号柜', 'code': 'A02', 'area': 'A区'},
            {'name': 'B区1号柜', 'code': 'B01', 'area': 'B区'},
            {'name': 'B区2号柜', 'code': 'B02', 'area': 'B区'},
            {'name': 'C区1号柜', 'code': 'C01', 'area': 'C区'},
        ]
        for loc in locations:
            StorageLocation.objects.get_or_create(**loc)
        self.stdout.write(self.style.SUCCESS('初始化库位数据'))

        laptop_type = EquipmentType.objects.get(code='LAPTOP')
        projector_type = EquipmentType.objects.get(code='PROJECTOR')
        camera_type = EquipmentType.objects.get(code='CAMERA')

        borrow_rules = [
            {'name': '笔记本电脑借用规则', 'equipment_type': laptop_type, 'max_borrow_days': 30, 'max_borrow_quantity': 2},
            {'name': '投影仪借用规则', 'equipment_type': projector_type, 'max_borrow_days': 7, 'max_borrow_quantity': 1},
            {'name': '摄像机借用规则', 'equipment_type': camera_type, 'max_borrow_days': 14, 'max_borrow_quantity': 1},
        ]
        for rule in borrow_rules:
            BorrowRule.objects.get_or_create(name=rule['name'], defaults=rule)
        self.stdout.write(self.style.SUCCESS('初始化借用规则数据'))

        a01 = StorageLocation.objects.get(code='A01')
        a02 = StorageLocation.objects.get(code='A02')
        b01 = StorageLocation.objects.get(code='B01')

        equipments = [
            {'serial_number': 'LAP001', 'name': 'ThinkPad X1 Carbon', 'equipment_type': laptop_type, 'storage_location': a01, 'specification': 'i7/16G/512G'},
            {'serial_number': 'LAP002', 'name': 'MacBook Pro 14', 'equipment_type': laptop_type, 'storage_location': a01, 'specification': 'M3/16G/512G'},
            {'serial_number': 'LAP003', 'name': 'Dell XPS 15', 'equipment_type': laptop_type, 'storage_location': a02, 'specification': 'i9/32G/1T'},
            {'serial_number': 'PRO001', 'name': 'Epson CB-X06', 'equipment_type': projector_type, 'storage_location': b01, 'specification': '3600流明'},
            {'serial_number': 'PRO002', 'name': 'BenQ MX560', 'equipment_type': projector_type, 'storage_location': b01, 'specification': '4000流明'},
            {'serial_number': 'CAM001', 'name': 'Sony FX3', 'equipment_type': camera_type, 'storage_location': a02, 'specification': '全画幅'},
            {'serial_number': 'CAM002', 'name': 'Canon R5', 'equipment_type': camera_type, 'storage_location': a02, 'specification': '8K视频'},
        ]
        for equip in equipments:
            Equipment.objects.get_or_create(serial_number=equip['serial_number'], defaults=equip)
        self.stdout.write(self.style.SUCCESS('初始化器材数据'))

        self.stdout.write(self.style.SUCCESS('数据初始化完成！'))
