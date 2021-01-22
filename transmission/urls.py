from django.urls import path
from .views import APIErrorView

urlpatterns = [
    path('api-errors/', APIErrorView.as_view(), name='transmission-api-error')
]
