from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone
from core.models import (
    EquipmentType, StorageLocation, BorrowRule, Equipment,
    PatrolBatch, PatrolRecord, EquipmentRepairOrder
)
from datetime import date, timedelta


class Command(BaseCommand):
    help = '初始化测试数据'

    def handle(self, *args, **options):
        self.stdout.write('开始初始化数据...')

        uploader_group, _ = Group.objects.get_or_create(name='uploader')
        reviewer_group, _ = Group.objects.get_or_create(name='reviewer')
        self.stdout.write(self.style.SUCCESS('创建用户组: uploader, reviewer'))

        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'a****@***********', 'admin123')
            self.stdout.write(self.style.SUCCESS('创建管理员用户: admin / admin123'))

        if not User.objects.filter(username='employee_a').exists():
            user_a = User.objects.create_user('employee_a', 'e***********@***********', 'emp123456')
            user_a.groups.add(uploader_group)
            self.stdout.write(self.style.SUCCESS('创建员工A用户(上传员): employee_a / emp123456'))

        if not User.objects.filter(username='employee_b').exists():
            user_b = User.objects.create_user('employee_b', 'e***********@***********', 'emp123456')
            user_b.groups.add(reviewer_group)
            self.stdout.write(self.style.SUCCESS('创建员工B用户(复核员): employee_b / emp123456'))

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

        if not PatrolBatch.objects.filter(batch_no='PTEST001').exists():
            admin_user = User.objects.get(username='admin')
            test_batch = PatrolBatch.objects.create(
                batch_no='PTEST001',
                uploader=admin_user,
                file_name='test_data.csv',
                total_count=3,
                success_count=3,
                problem_count=0,
                remark='测试批次'
            )

            lap001 = Equipment.objects.get(serial_number='LAP001')
            lap002 = Equipment.objects.get(serial_number='LAP002')
            pro001 = Equipment.objects.get(serial_number='PRO001')

            today = date.today()
            borrow_date = today - timedelta(days=30)
            due_date = today - timedelta(days=10)

            PatrolRecord.objects.create(
                batch=test_batch,
                line_number=1,
                equipment=lap001,
                equipment_serial='LAP001',
                equipment_name='ThinkPad X1 Carbon',
                equipment_type=lap001.equipment_type,
                storage_location=lap001.storage_location,
                location_code=lap001.storage_location.code,
                borrower='张三',
                borrow_date=borrow_date,
                due_date=due_date,
                return_date=today - timedelta(days=5),
                is_returned=True,
                damage_level=1,
                damage_description='键盘按键轻微磨损',
                status='approved',
                reviewer=admin_user,
                review_time=timezone.now(),
                review_remark='复核通过'
            )

            PatrolRecord.objects.create(
                batch=test_batch,
                line_number=2,
                equipment=lap002,
                equipment_serial='LAP002',
                equipment_name='MacBook Pro 14',
                equipment_type=lap002.equipment_type,
                storage_location=lap002.storage_location,
                location_code=lap002.storage_location.code,
                borrower='李四',
                borrow_date=borrow_date,
                due_date=due_date,
                return_date=today - timedelta(days=3),
                is_returned=True,
                damage_level=2,
                damage_description='屏幕有划痕，外壳有凹陷',
                status='approved',
                reviewer=admin_user,
                review_time=timezone.now(),
                review_remark='复核通过'
            )

            PatrolRecord.objects.create(
                batch=test_batch,
                line_number=3,
                equipment=pro001,
                equipment_serial='PRO001',
                equipment_name='Epson CB-X06',
                equipment_type=pro001.equipment_type,
                storage_location=pro001.storage_location,
                location_code=pro001.storage_location.code,
                borrower='王五',
                borrow_date=borrow_date,
                due_date=due_date,
                return_date=today - timedelta(days=1),
                is_returned=True,
                damage_level=3,
                damage_description='投影镜头模糊，无法正常聚焦',
                status='approved',
                reviewer=admin_user,
                review_time=timezone.now(),
                review_remark='复核通过'
            )

            self.stdout.write(self.style.SUCCESS('初始化测试巡管记录数据'))

            lap001.damage_level = 1
            lap001.save()
            lap002.damage_level = 2
            lap002.save()
            pro001.damage_level = 3
            pro001.save()
            self.stdout.write(self.style.SUCCESS('同步器材损坏等级'))

        self.stdout.write(self.style.SUCCESS('数据初始化完成！'))
