import csv
import io
import os
from datetime import datetime, timedelta
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .models import (
    EquipmentType, StorageLocation, BorrowRule, Equipment,
    PatrolBatch, PatrolRecord, ProblemRecord, EquipmentRepairOrder,
    DAMAGE_LEVEL_CHOICES, REPAIR_STATUS_CHOICES
)
from .serializers import (
    EquipmentTypeSerializer, StorageLocationSerializer, BorrowRuleSerializer,
    EquipmentSerializer, PatrolBatchSerializer, PatrolRecordSerializer,
    ProblemRecordSerializer, ReviewSerializer,
    EquipmentRepairOrderSerializer, RepairStatusUpdateSerializer, RepairOrderCreateSerializer
)
from .permissions import IsAdminUser, IsAdminOrReadOnly, IsUploader, IsReviewer


class EquipmentTypeViewSet(viewsets.ModelViewSet):
    queryset = EquipmentType.objects.all()
    serializer_class = EquipmentTypeSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']


class StorageLocationViewSet(viewsets.ModelViewSet):
    queryset = StorageLocation.objects.all()
    serializer_class = StorageLocationSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code', 'area']


class BorrowRuleViewSet(viewsets.ModelViewSet):
    queryset = BorrowRule.objects.all()
    serializer_class = BorrowRuleSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'equipment_type__name']


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['serial_number', 'name', 'specification']

    def get_queryset(self):
        queryset = super().get_queryset()
        equipment_type = self.request.query_params.get('equipment_type')
        storage_location = self.request.query_params.get('storage_location')
        damage_level = self.request.query_params.get('damage_level')
        is_available = self.request.query_params.get('is_available')

        if equipment_type:
            queryset = queryset.filter(equipment_type_id=equipment_type)
        if storage_location:
            queryset = queryset.filter(storage_location_id=storage_location)
        if damage_level:
            queryset = queryset.filter(damage_level=damage_level)
        if is_available is not None:
            queryset = queryset.filter(is_available=(is_available.lower() == 'true'))

        return queryset


class PatrolBatchViewSet(viewsets.ModelViewSet):
    queryset = PatrolBatch.objects.all()
    serializer_class = PatrolBatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(uploader=self.request.user)
        return queryset


class PatrolRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PatrolRecord.objects.all()
    serializer_class = PatrolRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['equipment_serial', 'equipment_name', 'borrower']

    def get_queryset(self):
        queryset = super().get_queryset()

        equipment_type = self.request.query_params.get('equipment_type')
        storage_location = self.request.query_params.get('storage_location')
        borrower = self.request.query_params.get('borrower')
        status = self.request.query_params.get('status')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        damage_level = self.request.query_params.get('damage_level')
        batch_id = self.request.query_params.get('batch_id')

        if equipment_type:
            queryset = queryset.filter(equipment_type_id=equipment_type)
        if storage_location:
            queryset = queryset.filter(storage_location_id=storage_location)
        if borrower:
            queryset = queryset.filter(borrower__icontains=borrower)
        if status:
            queryset = queryset.filter(status=status)
        if start_date:
            queryset = queryset.filter(borrow_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(borrow_date__lte=end_date)
        if damage_level:
            queryset = queryset.filter(damage_level=damage_level)
        if batch_id:
            queryset = queryset.filter(batch_id=batch_id)

        return queryset


class ProblemRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProblemRecord.objects.all()
    serializer_class = ProblemRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        batch_id = self.request.query_params.get('batch_id')
        is_resolved = self.request.query_params.get('is_resolved')
        problem_type = self.request.query_params.get('problem_type')

        if batch_id:
            queryset = queryset.filter(batch_id=batch_id)
        if is_resolved is not None:
            queryset = queryset.filter(is_resolved=(is_resolved.lower() == 'true'))
        if problem_type:
            queryset = queryset.filter(problem_type=problem_type)

        return queryset

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def resolve(self, request, pk=None):
        problem = self.get_object()
        resolution_note = request.data.get('resolution_note', '')
        problem.is_resolved = True
        problem.resolved_by = request.user
        problem.resolved_at = timezone.now()
        problem.resolution_note = resolution_note
        problem.save()
        return Response(ProblemRecordSerializer(problem).data)


class EquipmentRepairOrderViewSet(viewsets.ModelViewSet):
    queryset = EquipmentRepairOrder.objects.all()
    serializer_class = EquipmentRepairOrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['order_no', 'equipment__serial_number', 'equipment__name']

    def get_queryset(self):
        queryset = super().get_queryset()

        equipment_serial = self.request.query_params.get('equipment_serial')
        equipment_type = self.request.query_params.get('equipment_type')
        storage_location = self.request.query_params.get('storage_location')
        repair_person = self.request.query_params.get('repair_person')
        status = self.request.query_params.get('status')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if equipment_serial:
            queryset = queryset.filter(equipment__serial_number__icontains=equipment_serial)
        if equipment_type:
            queryset = queryset.filter(equipment__equipment_type_id=equipment_type)
        if storage_location:
            queryset = queryset.filter(equipment__storage_location_id=storage_location)
        if repair_person:
            queryset = queryset.filter(repair_person_id=repair_person)
        if status:
            queryset = queryset.filter(status=status)
        if start_date:
            queryset = queryset.filter(send_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(send_time__date__lte=end_date)

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return RepairOrderCreateSerializer
        return EquipmentRepairOrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        patrol_record = PatrolRecord.objects.get(id=validated_data['patrol_record_id'])
        repair_person = User.objects.get(id=validated_data['repair_person'])
        
        order_no = f'R{timezone.now().strftime("%Y%m%d%H%M%S")}'
        
        repair_order = EquipmentRepairOrder.objects.create(
            order_no=order_no,
            patrol_record=patrol_record,
            equipment=patrol_record.equipment,
            repair_reason=validated_data['repair_reason'],
            damage_description=validated_data['damage_description'],
            send_time=validated_data['send_time'],
            expected_complete_time=validated_data.get('expected_complete_time'),
            repair_person=repair_person,
            created_by=request.user
        )
        
        equipment = patrol_record.equipment
        equipment.is_available = False
        equipment.save()
        
        return Response(
            EquipmentRepairOrderSerializer(repair_order, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def update_status(self, request, pk=None):
        repair_order = self.get_object()
        serializer = RepairStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data['status']
        result_note = serializer.validated_data.get('result_note', '')
        updated_damage_level = serializer.validated_data.get('updated_damage_level')
        restore_available = serializer.validated_data.get('restore_available', True)
        
        repair_order.status = new_status
        repair_order.result_note = result_note
        
        if new_status == 'completed':
            repair_order.actual_complete_time = timezone.now()
            if updated_damage_level is not None:
                repair_order.updated_damage_level = updated_damage_level
            
            equipment = repair_order.equipment
            if updated_damage_level is not None:
                equipment.damage_level = updated_damage_level
            if restore_available:
                equipment.is_available = True
            equipment.save()
        elif new_status == 'cancelled':
            equipment = repair_order.equipment
            equipment.is_available = True
            equipment.save()
        
        repair_order.save()
        
        return Response(EquipmentRepairOrderSerializer(repair_order, context=self.get_serializer_context()).data)


class UploadBatchView(APIView):
    permission_classes = [IsUploader]

    ALLOWED_EXTENSIONS = ['.csv']
    ALLOWED_CONTENT_TYPES = ['text/csv', 'application/csv', 'text/plain', 'application/vnd.ms-excel']
    REQUIRED_COLUMNS = ['器材编号', '器材名称', '库位编码', '借用人', '借用日期', '应还日期', '归还日期', '是否归还', '损坏等级', '损坏描述']

    def post(self, request):
        if 'file' not in request.FILES:
            return Response({'error': '请上传CSV文件'}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']
        file_name = file.name
        file_ext = os.path.splitext(file_name)[1].lower()

        if file_ext not in self.ALLOWED_EXTENSIONS:
            return Response({'error': f'不支持的文件类型，仅支持: {", ".join(self.ALLOWED_EXTENSIONS)}'}, status=status.HTTP_400_BAD_REQUEST)

        content_type = file.content_type
        if content_type not in self.ALLOWED_CONTENT_TYPES and not file_name.endswith('.csv'):
            return Response({'error': '文件格式错误，请上传CSV格式文件'}, status=status.HTTP_400_BAD_REQUEST)

        remark = request.data.get('remark', '')

        try:
            file_content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            file.seek(0)
            try:
                file_content = file.read().decode('gbk')
            except UnicodeDecodeError:
                return Response({'error': '文件编码不支持，请使用UTF-8或GBK编码'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            csv_reader = csv.DictReader(io.StringIO(file_content))
        except Exception as e:
            return Response({'error': f'CSV文件解析失败: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        if csv_reader.fieldnames is None:
            return Response({'error': 'CSV文件格式错误，缺少表头'}, status=status.HTTP_400_BAD_REQUEST)

        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in csv_reader.fieldnames]
        if missing_columns:
            return Response({'error': f'CSV缺少必要列: {", ".join(missing_columns)}'}, status=status.HTTP_400_BAD_REQUEST)

        rows = list(csv_reader)

        if not rows:
            return Response({'error': 'CSV文件为空'}, status=status.HTTP_400_BAD_REQUEST)

        batch_no = f'P{timezone.now().strftime("%Y%m%d%H%M%S")}'
        batch = PatrolBatch.objects.create(
            batch_no=batch_no,
            uploader=request.user,
            file_name=file.name,
            remark=remark,
            total_count=len(rows)
        )

        success_count = 0
        problem_count = 0
        problem_records = []

        valid_damage_levels = [level[0] for level in DAMAGE_LEVEL_CHOICES]

        for idx, row in enumerate(rows, start=1):
            problems = []

            equipment_serial = str(row.get('器材编号', '')).strip()
            equipment_name = str(row.get('器材名称', '')).strip()
            location_code = str(row.get('库位编码', '')).strip()
            borrower = str(row.get('借用人', '')).strip()
            borrow_date_str = str(row.get('借用日期', '')).strip()
            due_date_str = str(row.get('应还日期', '')).strip()
            return_date_str = str(row.get('归还日期', '')).strip()
            is_returned_str = str(row.get('是否归还', '')).strip().lower()
            damage_level_str = str(row.get('损坏等级', '')).strip()
            damage_description = str(row.get('损坏描述', '')).strip()

            if not equipment_serial:
                problems.append(('missing_serial', '器材编号缺失'))

            storage_location = None
            if not location_code:
                problems.append(('invalid_location', '库位编码缺失'))
            else:
                try:
                    storage_location = StorageLocation.objects.get(code=location_code)
                except StorageLocation.DoesNotExist:
                    problems.append(('invalid_location', f'库位编码 {location_code} 不存在'))

            borrow_date = None
            due_date = None
            return_date = None

            try:
                borrow_date = datetime.strptime(borrow_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                problems.append(('time_inversion', '借用日期格式错误'))

            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                problems.append(('time_inversion', '应还日期格式错误'))

            if return_date_str:
                try:
                    return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    problems.append(('time_inversion', '归还日期格式错误'))

            if borrow_date and due_date and borrow_date > due_date:
                problems.append(('time_inversion', '借用日期晚于应还日期'))

            if return_date and borrow_date and return_date < borrow_date:
                problems.append(('time_inversion', '归还日期早于借用日期'))

            is_returned = is_returned_str in ['是', 'true', '1', 'yes']
            if is_returned and not return_date:
                problems.append(('return_conflict', '已归还但无归还日期'))
            if not is_returned and return_date:
                problems.append(('return_conflict', '未归还但有归还日期'))

            damage_level = 0
            if damage_level_str:
                try:
                    damage_level = int(damage_level_str)
                    if damage_level not in valid_damage_levels:
                        problems.append(('damage_out_of_range', f'损坏等级 {damage_level} 超出范围（0-4）'))
                except (ValueError, TypeError):
                    problems.append(('damage_out_of_range', f'损坏等级 {damage_level_str} 格式错误'))

            equipment = None
            if equipment_serial and not problems:
                try:
                    equipment = Equipment.objects.get(serial_number=equipment_serial)
                except Equipment.DoesNotExist:
                    problems.append(('equipment_not_found', f'器材编号 {equipment_serial} 不存在'))

            if problems:
                problem_count += 1
                problem_detail = '; '.join([p[1] for p in problems])
                problem_type = problems[0][0]
                problem_record = ProblemRecord.objects.create(
                    batch=batch,
                    line_number=idx,
                    problem_type=problem_type,
                    problem_detail=problem_detail,
                    row_data=row
                )
                problem_records.append(problem_record)
            else:
                success_count += 1
                PatrolRecord.objects.create(
                    batch=batch,
                    line_number=idx,
                    equipment=equipment,
                    equipment_serial=equipment_serial,
                    equipment_name=equipment_name,
                    equipment_type=equipment.equipment_type if equipment else None,
                    storage_location=storage_location,
                    location_code=location_code,
                    borrower=borrower,
                    borrow_date=borrow_date,
                    due_date=due_date,
                    return_date=return_date,
                    is_returned=is_returned,
                    damage_level=damage_level,
                    damage_description=damage_description
                )

        batch.success_count = success_count
        batch.problem_count = problem_count
        batch.save()

        response_data = {
            'batch_no': batch_no,
            'total_count': len(rows),
            'success_count': success_count,
            'problem_count': problem_count,
            'problem_records': ProblemRecordSerializer(problem_records, many=True).data
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class ReviewView(APIView):
    permission_classes = [IsReviewer]

    def post(self, request):
        serializer = ReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        record_ids = serializer.validated_data['record_ids']
        review_status = serializer.validated_data['status']
        remark = serializer.validated_data.get('remark', '')

        records_query = PatrolRecord.objects.filter(
            id__in=record_ids,
            status='pending'
        )

        records_list = list(records_query.select_related('equipment'))

        if not records_list:
            return Response({'error': '没有找到待复核的记录'}, status=status.HTTP_400_BAD_REQUEST)

        updated_count = records_query.update(
            status=review_status,
            reviewer=request.user,
            review_time=timezone.now(),
            review_remark=remark
        )

        if review_status == 'approved':
            for record in records_list:
                if record.equipment:
                    equipment = record.equipment
                    equipment.damage_level = record.damage_level
                    if record.is_returned:
                        equipment.is_available = True
                    else:
                        equipment.is_available = False
                    equipment.save()

        return Response({
            'message': f'成功复核 {updated_count} 条记录',
            'updated_count': updated_count,
            'status': review_status
        })


class StatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats_type = request.query_params.get('type', 'overview')

        if stats_type == 'pending_review':
            return self.get_pending_review()
        elif stats_type == 'damage_ranking':
            return self.get_damage_ranking()
        elif stats_type == 'delay_ranking':
            return self.get_delay_ranking()
        elif stats_type == 'repair_stats':
            return self.get_repair_stats()
        elif stats_type == 'frequent_damage_ranking':
            return self.get_frequent_damage_ranking()
        else:
            return self.get_overview()

    def get_pending_review(self):
        pending_records = PatrolRecord.objects.filter(status='pending')
        grouped = pending_records.values('batch__batch_no').annotate(
            count=Count('id')
        ).order_by('-count')

        return Response({
            'total_pending': pending_records.count(),
            'by_batch': [
                {
                    'batch_no': item['batch__batch_no'],
                    'count': item['count']
                }
                for item in grouped
            ],
            'records': PatrolRecordSerializer(pending_records[:50], many=True).data
        })

    def get_damage_ranking(self):
        records = PatrolRecord.objects.filter(
            damage_level__gt=0,
            status='approved'
        ).values(
            'equipment_type__name',
            'equipment_type__code'
        ).annotate(
            count=Count('id')
        ).order_by('-count')

        return Response({
            'ranking': [
                {
                    'equipment_type_name': item['equipment_type__name'],
                    'equipment_type_code': item['equipment_type__code'],
                    'damage_count': item['count']
                }
                for item in records
            ]
        })

    def get_delay_ranking(self):
        today = timezone.now().date()
        delayed_records = PatrolRecord.objects.filter(
            is_returned=False,
            due_date__lt=today,
            status='approved'
        )

        delayed_by_borrower = delayed_records.values('borrower').annotate(
            count=Count('id'),
        ).order_by('-count')[:20]

        ranking = []
        for item in delayed_by_borrower:
            borrower_records = delayed_records.filter(borrower=item['borrower'])
            total_delay_days = sum(
                (today - record.due_date).days
                for record in borrower_records
            )
            ranking.append({
                'borrower': item['borrower'],
                'delay_count': item['count'],
                'total_delay_days': total_delay_days,
                'avg_delay_days': round(total_delay_days / item['count'], 1)
            })

        ranking.sort(key=lambda x: x['total_delay_days'], reverse=True)

        return Response({
            'total_delayed': delayed_records.count(),
            'ranking': ranking
        })

    def get_overview(self):
        today = timezone.now().date()

        total_batches = PatrolBatch.objects.count()
        total_records = PatrolRecord.objects.count()
        pending_count = PatrolRecord.objects.filter(status='pending').count()
        approved_count = PatrolRecord.objects.filter(status='approved').count()
        delayed_count = PatrolRecord.objects.filter(
            is_returned=False,
            due_date__lt=today,
            status='approved'
        ).count()
        damaged_count = PatrolRecord.objects.filter(
            damage_level__gt=0,
            status='approved'
        ).count()

        repairing_count = EquipmentRepairOrder.objects.filter(
            status__in=['pending', 'repairing']
        ).count()
        completed_repair_count = EquipmentRepairOrder.objects.filter(
            status='completed'
        ).count()

        return Response({
            'total_batches': total_batches,
            'total_records': total_records,
            'pending_count': pending_count,
            'approved_count': approved_count,
            'delayed_count': delayed_count,
            'damaged_count': damaged_count,
            'repairing_count': repairing_count,
            'completed_repair_count': completed_repair_count
        })

    def get_repair_stats(self):
        total_repair_orders = EquipmentRepairOrder.objects.count()
        repairing_count = EquipmentRepairOrder.objects.filter(
            status__in=['pending', 'repairing']
        ).count()
        completed_count = EquipmentRepairOrder.objects.filter(
            status='completed'
        ).count()
        cancelled_count = EquipmentRepairOrder.objects.filter(
            status='cancelled'
        ).count()

        repair_by_type = EquipmentRepairOrder.objects.values(
            'equipment__equipment_type__name',
            'equipment__equipment_type__code'
        ).annotate(
            count=Count('id')
        ).order_by('-count')

        repair_stats = []
        for item in repair_by_type:
            completed_by_type = EquipmentRepairOrder.objects.filter(
                equipment__equipment_type__code=item['equipment__equipment_type__code'],
                status='completed'
            ).count()
            repair_stats.append({
                'equipment_type_name': item['equipment__equipment_type__name'],
                'equipment_type_code': item['equipment__equipment_type__code'],
                'repair_count': item['count'],
                'completed_count': completed_by_type
            })

        return Response({
            'total_repair_orders': total_repair_orders,
            'repairing_count': repairing_count,
            'completed_count': completed_count,
            'cancelled_count': cancelled_count,
            'by_equipment_type': repair_stats
        })

    def get_frequent_damage_ranking(self):
        ranking = EquipmentRepairOrder.objects.values(
            'equipment__serial_number',
            'equipment__name',
            'equipment__equipment_type__name'
        ).annotate(
            repair_count=Count('id')
        ).order_by('-repair_count')[:20]

        result = []
        for item in ranking:
            equipment = Equipment.objects.get(serial_number=item['equipment__serial_number'])
            result.append({
                'serial_number': item['equipment__serial_number'],
                'name': item['equipment__name'],
                'equipment_type_name': item['equipment__equipment_type__name'],
                'repair_count': item['repair_count'],
                'current_damage_level': equipment.damage_level,
                'current_damage_level_display': equipment.get_damage_level_display(),
                'is_available': equipment.is_available
            })

        return Response({
            'ranking': result
        })
