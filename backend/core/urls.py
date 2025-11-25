from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

def api_root(request):
    return JsonResponse({
        'message': 'IST Africa Procure-to-Pay API',
        'version': '1.0',
        'endpoints': {
            'admin': '/admin/',
            'procurement_requests': '/api/procurement/requests/',
            'auth_token': '/api/token/',
            'auth_refresh': '/api/token/refresh/',
        },
        'documentation': {
            'swagger_ui': '/api/docs/',
            'redoc': '/api/redoc/',
            'openapi_schema': '/api/schema/',
            'admin_interface': '/admin/'
        }
    })

urlpatterns = [
    path('', api_root, name='api_root'),
    path('admin/', admin.site.urls),
    
    # API endpoints - Clean app separation
    path('api/auth/', include('authentication.urls')),  # Authentication app
    path('api/procurement/', include('procurement.urls')),  # Procurement app
    
    # JWT Token endpoints (legacy support)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
