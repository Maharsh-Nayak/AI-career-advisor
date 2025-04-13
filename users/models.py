from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from datetime import datetime

class CustomUser(AbstractUser):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    skills = models.TextField(blank=True, help_text="Enter skills separated by commas")
    saved_jobs = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"
    
    def get_skills_list(self):
        if not self.skills:
            return []
        return [skill.strip() for skill in self.skills.split(',')]
    
    def get_saved_jobs(self):
        """Returns the list of saved jobs with proper formatting"""
        jobs = []
        for job in self.saved_jobs:
            # Ensure all required fields are present
            formatted_job = {
                'title': job.get('title', ''),
                'company_name': job.get('company_name', ''),
                'location': job.get('location', 'Remote'),
                'url': job.get('url', ''),
                'source': job.get('source', 'External'),
                'relevance_score': job.get('relevance_score', None),
                'saved_at': job.get('saved_at', datetime.now().isoformat())
            }
            jobs.append(formatted_job)
        return jobs
    
    def save_job(self, job_data):
        """Saves a job to the user's profile"""
        # Check if job already exists
        job_url = job_data.get('url', '')
        for job in self.saved_jobs:
            if job.get('url') == job_url:
                return False
        
        # Add timestamp to job data
        job_data['saved_at'] = datetime.now().isoformat()
        
        # Ensure all required fields are present
        formatted_job = {
            'title': job_data.get('title', ''),
            'company_name': job_data.get('company_name', ''),
            'location': job_data.get('location', 'Remote'),
            'url': job_url,
            'source': job_data.get('source', 'External'),
            'relevance_score': job_data.get('relevance_score', None),
            'saved_at': job_data['saved_at']
        }
        
        self.saved_jobs.append(formatted_job)
        self.save()
        return True
    
    def remove_job(self, job_url):
        """Removes a job from saved jobs using the job URL"""
        initial_length = len(self.saved_jobs)
        self.saved_jobs = [job for job in self.saved_jobs if job.get('url') != job_url]
        
        if len(self.saved_jobs) < initial_length:
            self.save()
            return True
        return False

@receiver(post_save, sender=CustomUser)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    try:
        if created:
            Profile.objects.get_or_create(user=instance)
        else:
            Profile.objects.get_or_create(user=instance)
    except Exception as e:
        print(f"Error creating/updating profile: {str(e)}") 