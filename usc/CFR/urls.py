from django.urls import path

from . import views
from django.conf import settings


app_name = settings.CFR

urlpatterns = [
    path(
        f'collection/{settings.CFR}/',
        views.CollectionView.as_view(), name='collection'),

    path(
        f'{settings.CFR}/<str:slug_id>/',
        views.NodeView.as_view(), name='node'),

    path(
        f'{settings.CFR}/<str:slug_id>/html/',
        views.Content.as_view(), name='html'),
]
