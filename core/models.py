from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class EquipmentType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='类型名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='类型编码')
    description = models.TextField(blank=True, null=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'equipment_type'
        verbose_name = '器材类型'
        verbose_name_plural = '器材类型'

    def __str__(self):
        return self.name


class StorageLocation(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='库位名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='库位编码')
    area = models.CharField(max_length=100, verbose_name='区域')
    description = models.TextField(blank=True, null=True, verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'storage_location'
        verbose_name = '库位'
        verbose_name_plural = '库位'

    def __str__(self):
        return f'{self.code} - {self.name}'


class BorrowRule(models.Model):
    name = models.CharField(max_length=100, verbose_name='规则名称')
    equipment_type = models.ForeignKey(EquipmentType, on_delete=models.CASCADE, related_name='borrow_rules', verbose_name='器材类型')
    max_borrow_days = models.IntegerField(verbose_name='最大借用天数')
    max_borrow_quantity = models.IntegerField(default=1, verbose_name='最大借用数量')
    requires_approval = models.BooleanField(default=False, verbose_name='是否需要审批')
    description = models.TextField(blank=True, null=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'borrow_rule'
        verbose_name = '借用规则'
        verbose_name_plural = '借用规则'

    def __str__(self):
        return self.name


DAMAGE_LEVEL_CHOICES = [
    (0, '无损坏'),
    (1, '轻微损坏'),
    (2, '中度损坏'),
    (3, '严重损坏'),
    (4, '报废'),
]

STATUS_CHOICES = [
    ('pending', '待复核'),
    ('approved', '已通过'),
    ('rejected', '已驳回'),
]


class Equipment(models.Model):
    serial_number = models.CharField(max_length=100, unique=True, verbose_name='器材编号')
    name = models.CharField(max_length=200, verbose_name='器材名称')
    equipment_type = models.ForeignKey(EquipmentType, on_delete=models.PROTECT, related_name='equipments', verbose_name='器材类型')
    storage_location = models.ForeignKey(StorageLocation, on_delete=models.PROTECT, related_name='equipments', verbose_name='库位')
    specification = models.CharField(max_length=200, blank=True, null=True, verbose_name='规格型号')
    purchase_date = models.DateField(blank=True, null=True, verbose_name='采购日期')
    damage_level = models.IntegerField(choices=DAMAGE_LEVEL_CHOICES, default=0, verbose_name='损坏等级')
    is_available = models.BooleanField(default=True, verbose_name='是否可用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'equipment'
        verbose_name = '器材'
        verbose_name_plural = '器材'

    def __str__(self):
        return f'{self.serial_number} - {self.name}'


class PatrolBatch(models.Model):
    batch_no = models.CharField(max_length=50, unique=True, verbose_name='批次号')
    uploader = models.ForeignKey(User, on_delete=models.PROTECT, related_name='uploaded_batches', verbose_name='上传人')
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    total_count = models.IntegerField(default=0, verbose_name='总记录数')
    success_count = models.IntegerField(default=0, verbose_name='成功入库数')
    problem_count = models.IntegerField(default=0, verbose_name='问题记录数')
    file_name = models.CharField(max_length=255, verbose_name='文件名')
    remark = models.TextField(blank=True, null=True, verbose_name='备注')

    class Meta:
        db_table = 'patrol_batch'
        verbose_name = '巡管批次'
        verbose_name_plural = '巡管批次'
        ordering = ['-upload_time']

    def __str__(self):
        return self.batch_no


OVERDUE_HANDLE_STATUS_CHOICES = [
    ('pending', '待处理'),
    ('handled', '已处理'),
]


class PatrolRecord(models.Model):
    batch = models.ForeignKey(PatrolBatch, on_delete=models.CASCADE, related_name='records', verbose_name='所属批次')
    line_number = models.IntegerField(verbose_name='行号')
    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT, related_name='patrol_records', null=True, blank=True, verbose_name='器材')
    equipment_serial = models.CharField(max_length=100, verbose_name='器材编号')
    equipment_name = models.CharField(max_length=200, verbose_name='器材名称')
    equipment_type = models.ForeignKey(EquipmentType, on_delete=models.PROTECT, related_name='patrol_records', null=True, blank=True, verbose_name='器材类型')
    storage_location = models.ForeignKey(StorageLocation, on_delete=models.PROTECT, related_name='patrol_records', null=True, blank=True, verbose_name='库位')
    location_code = models.CharField(max_length=50, verbose_name='库位编码')
    borrower = models.CharField(max_length=100, verbose_name='借用人')
    borrow_date = models.DateField(verbose_name='借用日期')
    due_date = models.DateField(verbose_name='应还日期')
    return_date = models.DateField(null=True, blank=True, verbose_name='归还日期')
    is_returned = models.BooleanField(default=False, verbose_name='是否归还')
    damage_level = models.IntegerField(choices=DAMAGE_LEVEL_CHOICES, default=0, verbose_name='损坏等级')
    damage_description = models.TextField(blank=True, null=True, verbose_name='损坏描述')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    reviewer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reviewed_records', null=True, blank=True, verbose_name='复核人')
    review_time = models.DateTimeField(null=True, blank=True, verbose_name='复核时间')
    review_remark = models.TextField(blank=True, null=True, verbose_name='复核备注')
    overdue_handle_status = models.CharField(max_length=20, choices=OVERDUE_HANDLE_STATUS_CHOICES, null=True, blank=True, verbose_name='逾期处理状态')
    overdue_handled_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='handled_overdue_records', null=True, blank=True, verbose_name='逾期处理人')
    overdue_handled_at = models.DateTimeField(null=True, blank=True, verbose_name='逾期处理时间')
    overdue_handle_remark = models.TextField(blank=True, null=True, verbose_name='逾期处理备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'patrol_record'
        verbose_name = '巡管记录'
        verbose_name_plural = '巡管记录'
        ordering = ['-id']

    def __str__(self):
        return f'{self.batch.batch_no} - 行{self.line_number}'

    @property
    def is_overdue(self):
        if self.status != 'approved' or self.is_returned or not self.due_date:
            return False
        from django.utils import timezone
        today = timezone.now().date()
        return today > self.due_date

    @property
    def overdue_days(self):
        if not self.is_overdue:
            return 0
        from django.utils import timezone
        today = timezone.now().date()
        return (today - self.due_date).days


REPAIR_STATUS_CHOICES = [
    ('pending', '待维修'),
    ('repairing', '维修中'),
    ('completed', '已完成'),
    ('cancelled', '已取消'),
]

REPAIR_REASON_CHOICES = [
    ('normal_wear', '正常损耗'),
    ('accident', '意外损坏'),
    ('malfunction', '设备故障'),
    ('maintenance', '定期维护'),
    ('other', '其他'),
]

PROBLEM_TYPE_CHOICES = [
    ('missing_serial', '器材编号缺失'),
    ('invalid_location', '库位不存在'),
    ('time_inversion', '借用时间倒置'),
    ('return_conflict', '归还状态冲突'),
    ('damage_out_of_range', '损坏等级越界'),
    ('equipment_not_found', '器材不存在'),
    ('other', '其他'),
]


class ProblemRecord(models.Model):
    batch = models.ForeignKey(PatrolBatch, on_delete=models.CASCADE, related_name='problem_records', verbose_name='所属批次')
    line_number = models.IntegerField(verbose_name='行号')
    problem_type = models.CharField(max_length=30, choices=PROBLEM_TYPE_CHOICES, verbose_name='问题类型')
    problem_detail = models.TextField(verbose_name='问题详情')
    row_data = models.JSONField(verbose_name='原始行数据')
    is_resolved = models.BooleanField(default=False, verbose_name='是否已解决')
    resolved_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='resolved_problems', null=True, blank=True, verbose_name='处理人')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')
    resolution_note = models.TextField(blank=True, null=True, verbose_name='处理备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'problem_record'
        verbose_name = '问题记录'
        verbose_name_plural = '问题记录'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.batch.batch_no} - 行{self.line_number} - {self.get_problem_type_display()}'


class EquipmentRepairOrder(models.Model):
    order_no = models.CharField(max_length=50, unique=True, verbose_name='工单号')
    patrol_record = models.ForeignKey(PatrolRecord, on_delete=models.PROTECT, related_name='repair_orders', verbose_name='巡管记录')
    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT, related_name='repair_orders', verbose_name='器材')
    repair_reason = models.CharField(max_length=30, choices=REPAIR_REASON_CHOICES, verbose_name='维修原因')
    damage_description = models.TextField(verbose_name='损坏描述')
    send_time = models.DateTimeField(verbose_name='送修时间')
    expected_complete_time = models.DateTimeField(null=True, blank=True, verbose_name='预计完成时间')
    actual_complete_time = models.DateTimeField(null=True, blank=True, verbose_name='实际完成时间')
    repair_person = models.ForeignKey(User, on_delete=models.PROTECT, related_name='assigned_repairs', verbose_name='维修负责人')
    status = models.CharField(max_length=20, choices=REPAIR_STATUS_CHOICES, default='pending', verbose_name='处理状态')
    result_note = models.TextField(blank=True, null=True, verbose_name='结果说明')
    updated_damage_level = models.IntegerField(choices=DAMAGE_LEVEL_CHOICES, null=True, blank=True, verbose_name='维修后损坏等级')
    restore_available = models.BooleanField(default=True, verbose_name='恢复可用状态')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_repair_orders', verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'equipment_repair_order'
        verbose_name = '器材维修工单'
        verbose_name_plural = '器材维修工单'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.order_no} - {self.equipment.serial_number}'
