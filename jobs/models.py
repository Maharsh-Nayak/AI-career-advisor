from django.db import models
from django.conf import settings

class JobMarket(models.Model):
    title = models.CharField(max_length=100)
    required_skills = models.JSONField()

    def __str__(self):
        return self.title

class JobListing(models.Model):
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    url = models.URLField()
    source = models.CharField(max_length=50)
    location = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company_name}"

class NetworkingGoal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    goal_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Store the analysis results
    extracted_keywords = models.JSONField(default=dict, blank=True, null=True)
    industries = models.JSONField(default=list, blank=True, null=True)
    companies = models.JSONField(default=list, blank=True, null=True)
    roles = models.JSONField(default=list, blank=True, null=True)
    
    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"Networking Goal for {username} - {self.created_at.strftime('%Y-%m-%d')}" 