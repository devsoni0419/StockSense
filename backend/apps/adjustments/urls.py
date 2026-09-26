from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InventoryAdjustmentViewSet

router = DefaultRouter()
router.register(r'adjustments', InventoryAdjustmentViewSet, basename='adjustment')

urlpatterns = [
    path('', include(router.urls)),
]
