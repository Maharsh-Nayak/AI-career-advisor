from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def landing_page(request):
    """
    Landing page view that shows the main page for non-authenticated users
    and redirects authenticated users to their dashboard.
    """
    if request.user.is_authenticated:
        return redirect('users:profile')
    return render(request, 'landing.html')

@login_required
def dashboard(request):
    """
    Dashboard view for authenticated users.
    """
    return render(request, 'dashboard.html') 