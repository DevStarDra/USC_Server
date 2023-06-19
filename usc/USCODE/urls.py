from django.urls import path
from django.conf import settings

from . import views

app_name = settings.USCODE

urlpatterns = [
    path(
        f'collection/{settings.USCODE}/',
        views.CollectionView.as_view(), name='collection'),
    path(
        'view/<str:slug_id>/',
        views.NodeView.as_view(), name='node'),
    path(
        'content/<str:slug_id>/',
        views.LeafView.as_view(), name='leaf'),
]
