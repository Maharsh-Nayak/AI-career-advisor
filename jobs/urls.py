from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/job-analysis/', views.job_analysis, name='job_analysis'),
] 