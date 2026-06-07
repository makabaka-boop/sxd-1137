from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    EquipmentType, StorageLocation, BorrowRule, Equipment,
    PatrolBatch, PatrolRecord, ProblemRecord,
    DAMAGE_LEVEL_CHOICES, STATUS_CHOICES
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
