"""
URL Configuration for F1 Data Platform.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse({'status': 'healthy', 'service': 'f1-django-api'})

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Health check
    path('health/', health_check, name='health'),

    # API endpoints
    path('api/', include('api.urls')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
