from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from .forms import UserRegistrationForm, UserLoginForm, ProfileUpdateForm, UserUpdateForm
from .models import Profile
from django.contrib.auth.models import User
import json
from django.http import JsonResponse

def send_verification_email(user, request):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verification_url = request.build_absolute_uri(f'/users/verify-email/{uid}/{token}/')
    
    subject = 'Verify your CareerPath AI account'
    message = render_to_string('users/email/verify_email.html', {
        'user': user,
        'verification_url': verification_url
    })
    
    send_mail(
        subject,
        message,
        'noreply@careerpathai.com',
        [user.email],
        html_message=message,
        fail_silently=False,
    )

def register_view(request):
    """
    View for user registration.
    Creates a new user account and logs them in.
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in after registration
            login(request, user)
            messages.success(request, "Your account has been created successfully!")
            return redirect('users:profile')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})

def verify_email(request, uidb64, token):
    """
    View for email verification.
    Verifies the user's email and activates their account.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your email has been verified! You can now login.")
        return redirect('users:login')
    else:
        messages.error(request, "The verification link was invalid or has expired.")
        return redirect('users:login')

def login_view(request):
    """
    View for user login.
    Authenticates the user and logs them in.
    """
    # Redirect if user is already logged in
    if request.user.is_authenticated:
        return redirect('users:profile')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('users:profile')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = UserLoginForm()
    
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    """
    View for user logout.
    Logs the user out and redirects to the login page.
    """
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('users:login')

@login_required
def profile_view(request):
    """
    View for user profile.
    Shows user information and allows profile updates.
    """
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('users:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    
    return render(request, 'users/profile.html', context)

@login_required
def profile_update_view(request):
    """
    View for updating user profile.
    Allows the user to update their profile information.
    """
    # Get or create profile
    profile = Profile.create_profile(request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('users:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    
    return render(request, 'users/profile_update.html', context)

@login_required
def save_job_view(request):
    """
    View for saving a job.
    Saves a job to the user's profile.
    """
    if request.method == 'POST':
        try:
            job_data = json.loads(request.body)
            
            # Get or create profile
            profile = Profile.create_profile(request.user)
            
            success = profile.save_job(job_data)
            
            if success:
                return JsonResponse({'status': 'success', 'message': 'Job saved successfully'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Job already saved'})
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def remove_job_view(request, job_id):
    """
    View for removing a job.
    Removes a job from the user's profile.
    """
    if request.method == 'POST':
        # Get or create profile
        profile = Profile.create_profile(request.user)
        
        success = profile.remove_job(job_id)
        
        if success:
            messages.success(request, "Job removed from saved jobs.")
        else:
            messages.error(request, "Job not found in saved jobs.")
            
        return redirect('users:profile')
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}) 