from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InternalTransferViewSet

router = DefaultRouter()
router.register(r'transfers', InternalTransferViewSet, basename='transfer')

urlpatterns = [
    path('', include(router.urls)),
]
