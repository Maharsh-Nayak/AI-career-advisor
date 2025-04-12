from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.index, name='index'),
    path('skills-analysis/', views.skills_analysis, name='skills_analysis'),
    path('api/job-analysis/', views.job_analysis, name='job_analysis'),
    path('resume-upload/', views.resume_upload, name='resume_upload'),
    path('api/networking-analysis/', views.networking_analysis, name='networking_analysis'),
    path('job-listings/', views.job_listings, name='job_listings'),
    path('job-listings/<int:job_id>/', views.job_detail, name='job_detail'),
    path('search-jobs/', views.search_jobs, name='search_jobs'),
    path('recommended-jobs/', views.recommended_jobs, name='recommended_jobs'),
] 