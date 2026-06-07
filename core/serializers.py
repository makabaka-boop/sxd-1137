from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    EquipmentType, StorageLocation, BorrowRule, Equipment,
    PatrolBatch, PatrolRecord, ProblemRecord, EquipmentRepairOrder,
    DAMAGE_LEVEL_CHOICES, STATUS_CHOICES, REPAIR_STATUS_CHOICES, REPAIR_REASON_CHOICES,
    OVERDUE_HANDLE_STATUS_CHOICES
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_staff']
        read_only_fields = ['id']


class EquipmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentType
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class StorageLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageLocation
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class BorrowRuleSerializer(serializers.ModelSerializer):
    equipment_type_name = serializers.CharField(source='equipment_type.name', read_only=True)

    class Meta:
        model = BorrowRule
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class EquipmentSerializer(serializers.ModelSerializer):
    equipment_type_name = serializers.CharField(source='equipment_type.name', read_only=True)
    storage_location_name = serializers.CharField(source='storage_location.name', read_only=True)
    damage_level_display = serializers.CharField(source='get_damage_level_display', read_only=True)

    class Meta:
        model = Equipment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class PatrolBatchSerializer(serializers.ModelSerializer):
    uploader_name = serializers.CharField(source='uploader.username', read_only=True)

    class Meta:
        model = PatrolBatch
        fields = '__all__'
        read_only_fields = ['id', 'batch_no', 'upload_time', 'uploader', 'total_count', 'success_count', 'problem_count']


class PatrolRecordSerializer(serializers.ModelSerializer):
    batch_no = serializers.CharField(source='batch.batch_no', read_only=True)
    equipment_type_name = serializers.CharField(source='equipment_type.name', read_only=True)
    storage_location_name = serializers.CharField(source='storage_location.name', read_only=True)
    damage_level_display = serializers.CharField(source='get_damage_level_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True, allow_null=True)
    is_overdue = serializers.BooleanField(read_only=True)
    overdue_days = serializers.IntegerField(read_only=True)
    overdue_handle_status_display = serializers.CharField(source='get_overdue_handle_status_display', read_only=True)
    overdue_handled_by_name = serializers.CharField(source='overdue_handled_by.username', read_only=True, allow_null=True)

    class Meta:
        model = PatrolRecord
        fields = '__all__'
        read_only_fields = ['id', 'batch', 'line_number', 'created_at']


class ProblemRecordSerializer(serializers.ModelSerializer):
    batch_no = serializers.CharField(source='batch.batch_no', read_only=True)
    problem_type_display = serializers.CharField(source='get_problem_type_display', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.username', read_only=True, allow_null=True)

    class Meta:
        model = ProblemRecord
        fields = '__all__'
        read_only_fields = ['id', 'batch', 'line_number', 'problem_type', 'problem_detail', 'row_data', 'created_at']


class UploadResponseSerializer(serializers.Serializer):
    batch_no = serializers.CharField()
    total_count = serializers.IntegerField()
    success_count = serializers.IntegerField()
    problem_count = serializers.IntegerField()
    problem_records = ProblemRecordSerializer(many=True)


class ReviewSerializer(serializers.Serializer):
    record_ids = serializers.ListField(child=serializers.IntegerField())
    status = serializers.ChoiceField(choices=['approved', 'rejected'])
    remark = serializers.CharField(required=False, allow_blank=True)


class EquipmentRepairOrderSerializer(serializers.ModelSerializer):
    equipment_serial = serializers.CharField(source='equipment.serial_number', read_only=True)
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    equipment_type_name = serializers.CharField(source='equipment.equipment_type.name', read_only=True)
    storage_location_name = serializers.CharField(source='equipment.storage_location.name', read_only=True)
    storage_location_code = serializers.CharField(source='equipment.storage_location.code', read_only=True)
    repair_reason_display = serializers.CharField(source='get_repair_reason_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    repair_person_name = serializers.CharField(source='repair_person.username', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    updated_damage_level_display = serializers.CharField(source='get_updated_damage_level_display', read_only=True)
    patrol_record_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = EquipmentRepairOrder
        fields = '__all__'
        read_only_fields = ['id', 'order_no', 'created_at', 'updated_at', 'created_by']

    def validate_patrol_record_id(self, value):
        try:
            patrol_record = PatrolRecord.objects.get(id=value)
        except PatrolRecord.DoesNotExist:
            raise serializers.ValidationError('巡管记录不存在')
        
        if patrol_record.status != 'approved':
            raise serializers.ValidationError('只能从已通过复核的巡管记录创建维修工单')
        
        if patrol_record.damage_level == 0:
            raise serializers.ValidationError('该巡管记录无损坏，无需创建维修工单')
        
        if not patrol_record.equipment:
            raise serializers.ValidationError('该巡管记录未关联器材')
        
        if EquipmentRepairOrder.objects.filter(patrol_record=patrol_record, status__in=['pending', 'repairing']).exists():
            raise serializers.ValidationError('该巡管记录已有进行中的维修工单')
        
        return value

    def create(self, validated_data):
        patrol_record_id = validated_data.pop('patrol_record_id')
        patrol_record = PatrolRecord.objects.get(id=patrol_record_id)
        validated_data['patrol_record'] = patrol_record
        validated_data['equipment'] = patrol_record.equipment
        validated_data['created_by'] = self.context['request'].user
        
        from django.utils import timezone
        order_no = f'R{timezone.now().strftime("%Y%m%d%H%M%S")}'
        validated_data['order_no'] = order_no
        
        instance = super().create(validated_data)
        
        equipment = instance.equipment
        equipment.is_available = False
        equipment.save()
        
        return instance


class RepairStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['repairing', 'completed', 'cancelled'])
    result_note = serializers.CharField(required=False, allow_blank=True)
    updated_damage_level = serializers.ChoiceField(choices=DAMAGE_LEVEL_CHOICES, required=False, allow_null=True)
    restore_available = serializers.BooleanField(required=False, default=True)


class RepairOrderCreateSerializer(serializers.Serializer):
    patrol_record_id = serializers.IntegerField()
    repair_reason = serializers.ChoiceField(choices=[item[0] for item in REPAIR_REASON_CHOICES])
    damage_description = serializers.CharField()
    send_time = serializers.DateTimeField()
    expected_complete_time = serializers.DateTimeField(required=False, allow_null=True)
    repair_person = serializers.IntegerField()

    def validate_patrol_record_id(self, value):
        try:
            patrol_record = PatrolRecord.objects.get(id=value)
        except PatrolRecord.DoesNotExist:
            raise serializers.ValidationError('巡管记录不存在')
        
        if patrol_record.status != 'approved':
            raise serializers.ValidationError('只能从已通过复核的巡管记录创建维修工单')
        
        if patrol_record.damage_level == 0:
            raise serializers.ValidationError('该巡管记录无损坏，无需创建维修工单')
        
        if not patrol_record.equipment:
            raise serializers.ValidationError('该巡管记录未关联器材')
        
        if EquipmentRepairOrder.objects.filter(patrol_record=patrol_record, status__in=['pending', 'repairing']).exists():
            raise serializers.ValidationError('该巡管记录已有进行中的维修工单')
        
        return value

    def validate_repair_person(self, value):
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('维修负责人不存在')
        return value


class OverdueHandleSerializer(serializers.Serializer):
    record_ids = serializers.ListField(child=serializers.IntegerField())
    handle_remark = serializers.CharField(required=False, allow_blank=True)

    def validate_record_ids(self, value):
        if not value:
            raise serializers.ValidationError('请选择要处理的记录')
        
        from django.utils import timezone
        today = timezone.now().date()
        
        records = PatrolRecord.objects.filter(id__in=value)
        if records.count() != len(value):
            raise serializers.ValidationError('部分记录不存在')
        
        for record in records:
            if record.status != 'approved':
                raise serializers.ValidationError(f'记录 {record.id} 未通过复核，无法处理逾期')
            if record.is_returned:
                raise serializers.ValidationError(f'记录 {record.id} 已归还，不属于逾期记录')
            if record.due_date >= today:
                raise serializers.ValidationError(f'记录 {record.id} 未到逾期时间')
        
        return value
