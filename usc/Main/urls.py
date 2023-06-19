from django.urls import path
from django.views.generic import TemplateView

from . import views


app_name = 'main'

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.FullTextSearch.as_view(), name='search'),
    path('update-cookies/', views.update_cookies, name='update_cookies'),

    path(
        'terms-of-use/',
        TemplateView.as_view(template_name='Main/terms_of_use.html'),
        name='terms_of_use'
    ),
    path(
        'terms-of-service/',
        TemplateView.as_view(template_name='Main/terms_of_service.html'),
        name='terms_of_service'
    ),
    path(
        'privacy-policy/',
        TemplateView.as_view(template_name='Main/privacy_policy.html'),
        name='privacy_policy'
    ),
]
