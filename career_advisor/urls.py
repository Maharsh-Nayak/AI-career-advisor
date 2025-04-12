from django.contrib import admin
from django.urls import path, include
from frontend.views import home
from careerpath.views import landing_page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('landing/', landing_page, name='landing'),
    path('', include('jobs.urls')),
    path('', include('frontend.urls')),
    path('users/', include('users.urls')),
] 