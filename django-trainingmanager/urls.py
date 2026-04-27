from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # /api/v1/ : à câbler à l'étape 2 (DRF)
]

if settings.DEBUG:
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
