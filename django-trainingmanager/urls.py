from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Allauth headless (register, login, email confirmation, password reset)
    path('api/v1/auth/', include('allauth.headless.urls')),

    # Auth API (JWT)
    path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # CustomUser (/me/)
    path('api/v1/', include('customuser.urls')),

    # Endpoints métier
    path('api/v1/', include('agenda.urls')),
    path('api/v1/', include('event.urls')),
    path('api/v1/', include('round.urls')),
    path('api/v1/', include('exercise.urls')),
    path('api/v1/', include('member.urls')),

    # OpenAPI schema + Swagger UI
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
