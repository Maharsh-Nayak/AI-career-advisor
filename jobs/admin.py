from django.contrib import admin
from .models import JobMarket, JobListing

@admin.register(JobMarket)
class JobMarketAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)

@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company_name', 'source', 'location', 'created_at')
    list_filter = ('source', 'location')
    search_fields = ('title', 'company_name')
    readonly_fields = ('created_at',) 