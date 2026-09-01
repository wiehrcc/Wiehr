import os

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.views.generic import RedirectView

from . import settings as project_settings


urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^admin/$', RedirectView.as_view(url='/admin', permanent=False)),

    path('', include('web.urls')),
]

admin.site.site_header = '🌐'
admin.site.site_title = 'Wiehr'
admin.site.index_title = '𝄃𝄃𝄂𝄂𝄀𝄁𝄃𝄂𝄂𝄃'


if project_settings.ENV != 'PROD':
    from django.contrib.staticfiles.views import serve as staticfiles_serve
    from django.views.static import serve as media_serve

    _static_prefix = project_settings.STATIC_URL.strip('/')
    _media_prefix = project_settings.MEDIA_URL.strip('/')

    urlpatterns += [
        re_path(r'^%s/(?P<path>.*)$' % _static_prefix, staticfiles_serve,
                {'insecure': True}),
        re_path(r'^%s/(?P<path>.*)$' % _media_prefix, media_serve,
                {'document_root': project_settings.MEDIA_ROOT}),
    ]
else:
    urlpatterns += static(project_settings.MEDIA_URL, document_root=project_settings.MEDIA_ROOT)
    urlpatterns += static(project_settings.STATIC_URL, document_root=project_settings.STATIC_ROOT)


handler404 = 'web.views.handler404'
handler500 = 'web.views.handler500'
