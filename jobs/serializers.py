from rest_framework import serializers
from .models import JobMarket, JobListing

class JobMarketSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobMarket
        fields = ['title', 'required_skills']

class JobListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobListing
        fields = ['title', 'company_name', 'url', 'source', 'location', 'created_at'] 