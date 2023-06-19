from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Main.urls')),
    path('', include('USCODE.urls')),
    path('', include('CFR.urls')),
    path('', include('account.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += [
        # Debug toolbar url
        path('__debug__/', include("debug_toolbar.urls")),
    ]

    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
