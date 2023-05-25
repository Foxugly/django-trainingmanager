from django.apps import apps
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, include, reverse
from django.utils import translation

from customuser.views import CustomUserUpdateView


def home(request):
    c = {}
    available_apps = {}
    for app in apps.get_models():
        if not app.__module__.startswith("django"):
            a = app.__module__.split('.models')[0]
            if a in available_apps:
                available_apps[a].append(app)
            else:
                available_apps[a] = [app]
    c['apps'] = available_apps
    return render(request, "index.html", c)


def set_lang(request):
    response = None
    if 'lang' in request.GET and check_for_language(request.GET.get('lang')):
        user_language = request.GET.get('lang')
        translation.activate(user_language)
        if 'next' in request.GET:
            response = HttpResponseRedirect(request.GET.get('next'))
        else:
            response = HttpResponseRedirect(reverse('home'))
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            user_language,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path=settings.LANGUAGE_COOKIE_PATH,
            domain=settings.LANGUAGE_COOKIE_DOMAIN,
            secure=settings.LANGUAGE_COOKIE_SECURE,
            httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
            samesite=settings.LANGUAGE_COOKIE_SAMESITE,
        )
    return response


urlpatterns = [
    path('', home, name='index'),
    path('agenda/', include('agenda.urls', namespace='agenda')),
    path('event/', include('event.urls', namespace='event')),
    path('member/', include('member.urls', namespace='member')),
    path('round/', include('round.urls', namespace='round')),
    path('exercise/', include('exercise.urls', namespace='exercise')),
    path('lang/', set_lang, name='lang'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/update/', CustomUserUpdateView.as_view(), name='update_user'),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
