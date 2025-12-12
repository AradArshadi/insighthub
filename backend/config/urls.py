from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Insighthub API",
        default_version='v1',
        description="Business Intelligence Platform API",
        terms_of_service="https://insighthub.com/terms/",
        contact=openapi.Contact(email="support@insighthub.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API v1
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/businesses/', include('apps.businesses.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
    path('api/v1/ingestion/', include('apps.ingestion.urls')),
    path('api/v1/subscriptions/', include('apps.subscriptions.urls')),
    
    # Health check
    path('health/', include('health_check.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
    
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)