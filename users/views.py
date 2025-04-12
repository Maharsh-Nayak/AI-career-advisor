from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserLoginForm, ProfileUpdateForm, UserUpdateForm
from .models import Profile, TechNewsSubscription
from django.contrib.auth.models import User
import json
from django.http import JsonResponse
from .email_service import TechNewsEmailService

def register_view(request):
    if request.user.is_authenticated:
        return redirect('users:profile')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('users:profile')
        else:
            messages.error(request, "Registration failed. Please correct the errors.")
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
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
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('login')

@login_required
def profile_view(request):
    user = request.user
    profile = user.profile
    saved_jobs = profile.get_saved_jobs()
    
    context = {
        'user': user,
        'profile': profile,
        'saved_jobs': saved_jobs
    }
    
    return render(request, 'users/profile.html', context)

@login_required
def profile_update_view(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('users:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    
    return render(request, 'users/profile_update.html', context)

@login_required
def save_job_view(request):
    if request.method == 'POST':
        try:
            job_data = json.loads(request.body)
            profile = request.user.profile
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
    if request.method == 'POST':
        profile = request.user.profile
        success = profile.remove_job(job_id)
        
        if success:
            messages.success(request, "Job removed from saved jobs.")
        else:
            messages.error(request, "Job not found in saved jobs.")
            
        return redirect('users:profile')
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def tech_news_preferences(request):
    """View for managing technology news subscriptions"""
    user = request.user
    profile = user.profile
    
    # Get user's current subscriptions
    subscriptions = TechNewsSubscription.objects.filter(user=user).order_by('technology')
    
    if request.method == 'POST':
        # Handle toggling email updates
        if 'toggle_emails' in request.POST:
            profile.receive_news_updates = not profile.receive_news_updates
            profile.save()
            
            status = "enabled" if profile.receive_news_updates else "disabled"
            messages.success(request, f"Technology news updates {status} successfully!")
        
        # Handle adding a new technology subscription
        elif 'add_subscription' in request.POST:
            technology = request.POST.get('technology', '').strip().lower()
            
            if technology:
                if len(technology) < 3:
                    messages.error(request, "Technology name must be at least 3 characters.")
                else:
                    # Check if subscription already exists
                    if TechNewsSubscription.objects.filter(user=user, technology=technology).exists():
                        messages.info(request, f"You're already subscribed to {technology} news.")
                    else:
                        TechNewsSubscription.objects.create(user=user, technology=technology)
                        messages.success(request, f"Subscribed to {technology} news successfully!")
        
        # Handle removing a subscription
        elif 'remove_subscription' in request.POST:
            subscription_id = request.POST.get('subscription_id')
            if subscription_id:
                try:
                    subscription = TechNewsSubscription.objects.get(id=subscription_id, user=user)
                    tech_name = subscription.technology
                    subscription.delete()
                    messages.success(request, f"Unsubscribed from {tech_name} news.")
                except TechNewsSubscription.DoesNotExist:
                    messages.error(request, "Subscription not found.")
        
        # Handle sending a test email
        elif 'send_test_email' in request.POST:
            # Get technologies from subscriptions
            techs = list(subscriptions.values_list('technology', flat=True))
            
            if techs:
                from users.services import TechNewsService
                
                # Get a sample of news for each technology
                all_articles = []
                for tech in techs[:3]:  # Limit to 3 technologies for the test
                    articles = TechNewsService.fetch_news_for_technology(tech, limit=2)
                    saved_articles = TechNewsService.save_articles_to_db(articles)
                    all_articles.extend(saved_articles)
                
                if all_articles:
                    # Send the test email
                    sent = TechNewsEmailService.send_tech_news_email(user, all_articles)
                    if sent:
                        messages.success(request, "Test email sent successfully! Check your inbox.")
                    else:
                        messages.error(request, "Failed to send test email. Please try again later.")
                else:
                    messages.warning(request, "No news articles found for your technologies. Please try again later.")
            else:
                messages.warning(request, "You need to subscribe to at least one technology to receive test emails.")
        
        return redirect('tech_news_preferences')
    
    # Get all skills from user profile
    skills = profile.get_skills_list()
    
    # Create a list of technologies user might be interested in but isn't subscribed to
    subscribed_techs = [sub.technology for sub in subscriptions]
    suggested_techs = [skill for skill in skills if skill.lower() not in subscribed_techs]
    
    context = {
        'profile': profile,
        'subscriptions': subscriptions,
        'suggested_techs': suggested_techs[:5],  # Limit to 5 suggestions
    }
    
    return render(request, 'users/tech_news_preferences.html', context)

@login_required
def delete_subscription(request, subscription_id):
    """View for deleting a technology news subscription"""
    subscription = get_object_or_404(TechNewsSubscription, id=subscription_id, user=request.user)
    
    if request.method == 'POST':
        tech_name = subscription.technology
        subscription.delete()
        messages.success(request, f"Unsubscribed from {tech_name} news.")
    
    return redirect('tech_news_preferences') 