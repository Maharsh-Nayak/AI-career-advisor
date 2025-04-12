from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Profile, CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'unique_id', 'is_staff')
    search_fields = ('username', 'email', 'unique_id')
    readonly_fields = ('unique_id',)

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location')
    search_fields = ('user__username', 'user__email', 'location')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Profile, ProfileAdmin) 