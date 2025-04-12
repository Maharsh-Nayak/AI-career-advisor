from django.urls import path
from . import views

urlpatterns = [
    # ... existing code ...
    path('networking-analysis/', views.networking_analysis, name='networking_analysis'),
    # ... existing code ...
] 