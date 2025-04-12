from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    skills = models.TextField(blank=True, help_text="Enter skills separated by commas")
    saved_jobs = models.JSONField(default=list, blank=True)
    receive_news_updates = models.BooleanField(default=True, help_text="Receive news updates about technologies relevant to your skills")
    
    def __str__(self):
        return f"{self.user.username}'s profile"
    
    def get_skills_list(self):
        if not self.skills:
            return []
        return [skill.strip() for skill in self.skills.split(',')]
    
    def get_saved_jobs(self):
        return self.saved_jobs
    
    def save_job(self, job_data):
        # Check if job already exists
        job_id = job_data.get('id', job_data.get('title', ''))
        
        for job in self.saved_jobs:
            if job.get('id', job.get('title', '')) == job_id:
                return False
        
        self.saved_jobs.append(job_data)
        self.save()
        return True
    
    def remove_job(self, job_id):
        initial_length = len(self.saved_jobs)
        self.saved_jobs = [job for job in self.saved_jobs if job.get('id', job.get('title', '')) != job_id]
        
        if len(self.saved_jobs) < initial_length:
            self.save()
            return True
        return False

class TechNewsSubscription(models.Model):
    """Model to store user preferences for technology news updates"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tech_news_subscriptions')
    technology = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    last_notified = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'technology']
        verbose_name = "Technology News Subscription"
        verbose_name_plural = "Technology News Subscriptions"
    
    def __str__(self):
        return f"{self.user.username} - {self.technology}"

class NewsArticle(models.Model):
    """Model to store fetched news articles"""
    title = models.CharField(max_length=255)
    url = models.URLField()
    source = models.CharField(max_length=100)
    published_date = models.DateTimeField()
    technology = models.CharField(max_length=100)
    summary = models.TextField()
    
    class Meta:
        ordering = ['-published_date']
    
    def __str__(self):
        return self.title

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(post_save, sender=Profile)
def create_tech_subscriptions(sender, instance, created, **kwargs):
    """When a profile is updated with skills, create tech news subscriptions"""
    if instance.skills:
        skills = instance.get_skills_list()
        for skill in skills:
            # Only create subscriptions for technical skills
            if len(skill) > 2:  # Skip very short skill names
                TechNewsSubscription.objects.get_or_create(
                    user=instance.user,
                    technology=skill.lower()
                ) 