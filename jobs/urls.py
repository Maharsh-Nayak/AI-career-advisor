from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.job_listings, name='job_listings'),
    path('save/', views.save_job, name='save_job'),
    path('saved/', views.saved_jobs, name='saved_jobs'),
    path('search/', views.search_jobs, name='search_jobs'),
    path('recommended/', views.recommended_jobs, name='recommended_jobs'),
    path('detail/<int:job_id>/', views.job_detail, name='job_detail'),
    path('resume-upload/', views.resume_upload, name='resume_upload'),
    path('job-analysis/', views.job_analysis, name='job_analysis'),
    path('networking-analysis/', views.networking_analysis, name='networking_analysis'),
    path('trending-courses/', views.trending_courses, name='trending_courses'),
    path('test/resume-analysis/', views.test_resume_analysis, name='test_resume_analysis'),
    path('test/skill-extraction/', views.test_skill_extraction, name='test_skill_extraction'),
    path('skills-analysis/', views.skills_analysis, name='skills_analysis'),
] 