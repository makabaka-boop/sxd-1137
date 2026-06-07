from django.contrib import admin
from .models import (
    EquipmentType, StorageLocation, BorrowRule, Equipment,
    PatrolBatch, PatrolRecord, ProblemRecord, EquipmentRepairOrder
)


@admin.register(EquipmentType)
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'description', 'created_at']
    search_fields = ['name', 'code']
    list_filter = ['created_at']


@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'area', 'is_active', 'description']
    search_fields = ['name', 'code', 'area']
    list_filter = ['is_active', 'area']


@admin.register(BorrowRule)
class BorrowRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'equipment_type', 'max_borrow_days', 'max_borrow_quantity', 'requires_approval']
    search_fields = ['name', 'equipment_type__name']
    list_filter = ['requires_approval', 'equipment_type']


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['serial_number', 'name', 'equipment_type', 'storage_location', 'damage_level', 'is_available']
    search_fields = ['serial_number', 'name', 'specification']
    list_filter = ['equipment_type', 'storage_location', 'damage_level', 'is_available']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PatrolBatch)
class PatrolBatchAdmin(admin.ModelAdmin):
    list_display = ['batch_no', 'uploader', 'upload_time', 'total_count', 'success_count', 'problem_count']
    search_fields = ['batch_no', 'uploader__username', 'file_name']
    list_filter = ['upload_time']
    readonly_fields = ['batch_no', 'uploader', 'upload_time', 'total_count', 'success_count', 'problem_count']


@admin.register(PatrolRecord)
class PatrolRecordAdmin(admin.ModelAdmin):
    list_display = [
        'batch', 'line_number', 'equipment_serial', 'equipment_name', 
        'borrower', 'damage_level', 'status', 'is_returned',
        'return_date', 'return_storage_location', 'return_damage_level',
        'is_overdue_display', 'overdue_days_display', 'overdue_handle_status'
    ]
    search_fields = ['equipment_serial', 'equipment_name', 'borrower', 'batch__batch_no']
    list_filter = [
        'status', 'damage_level', 'equipment_type', 'storage_location',
        'overdue_handle_status', 'is_returned', 'return_storage_location',
        'return_damage_level', 'return_date'
    ]
    readonly_fields = ['batch', 'line_number', 'created_at', 'returned_by', 'returned_at']
    fieldsets = (
        (None, {
            'fields': ('batch', 'line_number', 'equipment', 'equipment_serial', 'equipment_name')
        }),
        ('借用信息', {
            'fields': ('equipment_type', 'storage_location', 'location_code', 'borrower', 
                       'borrow_date', 'due_date', 'return_date', 'is_returned')
        }),
        ('归还信息', {
            'fields': ('return_storage_location', 'return_damage_level', 'return_remark',
                       'returned_by', 'returned_at')
        }),
        ('损坏信息', {
            'fields': ('damage_level', 'damage_description')
        }),
        ('复核信息', {
            'fields': ('status', 'reviewer', 'review_time', 'review_remark')
        }),
        ('逾期处理', {
            'fields': ('overdue_handle_status', 'overdue_handled_by', 'overdue_handled_at', 'overdue_handle_remark')
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def is_overdue_display(self, obj):
        return obj.is_overdue
    is_overdue_display.boolean = True
    is_overdue_display.short_description = '是否逾期'

    def overdue_days_display(self, obj):
        return obj.overdue_days
    overdue_days_display.short_description = '逾期天数'


@admin.register(ProblemRecord)
class ProblemRecordAdmin(admin.ModelAdmin):
    list_display = ['batch', 'line_number', 'problem_type', 'is_resolved', 'resolved_by', 'resolved_at']
    search_fields = ['batch__batch_no', 'problem_detail']
    list_filter = ['problem_type', 'is_resolved']
    readonly_fields = ['batch', 'line_number', 'problem_type', 'problem_detail', 'row_data', 'created_at']


@admin.register(EquipmentRepairOrder)
class EquipmentRepairOrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_no', 'equipment', 'patrol_record', 'repair_reason',
        'repair_person', 'status', 'send_time', 'expected_complete_time'
    ]
    search_fields = ['order_no', 'equipment__serial_number', 'equipment__name', 'repair_person__username']
    list_filter = ['status', 'repair_reason', 'equipment__equipment_type', 'equipment__storage_location']
    readonly_fields = ['order_no', 'created_by', 'created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('order_no', 'patrol_record', 'equipment', 'created_by')
        }),
        ('维修信息', {
            'fields': ('repair_reason', 'damage_description', 'send_time', 'expected_complete_time', 'actual_complete_time')
        }),
        ('负责人与状态', {
            'fields': ('repair_person', 'status', 'result_note')
        }),
        ('维修结果', {
            'fields': ('updated_damage_level', 'restore_available')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
