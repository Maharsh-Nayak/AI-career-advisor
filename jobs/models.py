from django.db import models

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