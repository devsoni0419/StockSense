from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StockLedgerViewSet

router = DefaultRouter()
router.register(r'ledger', StockLedgerViewSet, basename='stockledger')

urlpatterns = [
    path('', include(router.urls)),
]
