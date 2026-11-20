from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('profile')
    return redirect('login')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('quizzes/', include('apps.quizzes.urls')),
    path('rooms/', include('apps.rooms.urls')),
    path('ai/', include('apps.ai.urls')),
    path('', home_redirect, name='home'),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()

