from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('networking-analysis/', views.networking_analysis, name='networking_analysis'),
] 