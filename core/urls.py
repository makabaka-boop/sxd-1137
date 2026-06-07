from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from . import views

router = DefaultRouter()
router.register(r'equipment-types', views.EquipmentTypeViewSet)
router.register(r'storage-locations', views.StorageLocationViewSet)
router.register(r'borrow-rules', views.BorrowRuleViewSet)
router.register(r'equipments', views.EquipmentViewSet)
router.register(r'patrol-batches', views.PatrolBatchViewSet)
router.register(r'patrol-records', views.PatrolRecordViewSet)
router.register(r'problem-records', views.ProblemRecordViewSet)

urlpatterns = [
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('upload/', views.UploadBatchView.as_view(), name='upload_batch'),
    path('review/', views.ReviewView.as_view(), name='review_records'),
    path('statistics/', views.StatisticsView.as_view(), name='statistics'),
    path('', include(router.urls)),
]
