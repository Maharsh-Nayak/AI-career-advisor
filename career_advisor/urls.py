from django.contrib import admin
from django.urls import path, include
from frontend.views import index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='home'),
    path('', include('jobs.urls')),
    path('', include('frontend.urls')),
    path('users/', include('users.urls')),
] 