from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PurchaseRequestViewSet, dashboard_stats

router = DefaultRouter()
router.register(r'requests', PurchaseRequestViewSet, basename='requests')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),
]
