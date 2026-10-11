from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/accounts/', include('accounts.urls')),
    path('api/v1/dashboard/', include('dashboard.urls')),
    path('api/v1/finance/', include('finance.urls')),
    path('auth/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('finance/', include('finance.urls')),
]
