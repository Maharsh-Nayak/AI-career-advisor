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

class CourseRecommendation(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('all_levels', 'All Levels'),
    ]

    PLATFORM_CHOICES = [
        ('coursera', 'Coursera'),
        ('udemy', 'Udemy'),
        ('edx', 'edX'),
        ('linkedin', 'LinkedIn Learning'),
        ('pluralsight', 'Pluralsight'),
        ('udacity', 'Udacity'),
        ('other', 'Other'),
    ]

    skill = models.CharField(max_length=100)
    course_title = models.CharField(max_length=200)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    url = models.URLField()
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    description = models.TextField()
    rating = models.FloatField(null=True, blank=True)
    reviews_count = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    duration_weeks = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['-rating', '-reviews_count']

    def __str__(self):
        return f"{self.course_title} ({self.platform}) - {self.skill}"

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