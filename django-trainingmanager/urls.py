from django.conf.urls import handler400, handler403, handler404, handler500
from django.contrib import admin
from django.urls import path, include, reverse
from django.conf.urls.static import static
from django.conf import settings
from django.apps import apps
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.utils import translation
from customuser.views import CustomUserUpdateView
from customuser.decorators import check_lang


@check_lang
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

def set_language(request):
    if 'lang' in request.GET and 'next' in request.GET:
        if translation.LANGUAGE_SESSION_KEY in request.session:
            del request.session[translation.LANGUAGE_SESSION_KEY]
        translation.activate(request.GET.get('lang'))
        request.session[translation.LANGUAGE_SESSION_KEY] = request.GET.get('lang')
        return HttpResponseRedirect(request.GET.get('next'))
    else:
        return reverse('home')


urlpatterns = [
    path('', home, name='index'),
    path('agenda/', include('agenda.urls', namespace='agenda')),
    path('event/', include('event.urls', namespace='event')),
    path('member/', include('member.urls', namespace='member')),
    path('round/', include('round.urls', namespace='round')),
    path('exercise/', include('exercise.urls', namespace='exercise')),
    path('lang/', set_language, name='lang'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/update/', check_lang(CustomUserUpdateView.as_view()), name='update_user'),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)