from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/', include('apps.products.urls')),
    path('api/', include('apps.warehouses.urls')),
    path('api/', include('apps.inventory.urls')),
    path('api/', include('apps.receipts.urls')),
    path('api/', include('apps.deliveries.urls')),
    path('api/', include('apps.transfers.urls')),
    path('api/', include('apps.adjustments.urls')),
    path('api/', include('apps.ledger.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('api/', include('apps.notifications.urls')),
]
