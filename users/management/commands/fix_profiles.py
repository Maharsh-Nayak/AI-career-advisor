from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import Profile

class Command(BaseCommand):
    help = 'Fixes issues with user profiles'

    def handle(self, *args, **options):
        # Get all users
        users = User.objects.all()
        
        # Count users without profiles
        users_without_profiles = 0
        for user in users:
            if not hasattr(user, 'profile'):
                Profile.objects.create(user=user)
                users_without_profiles += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {users_without_profiles} missing profiles'))
        
        # Check for duplicate profiles
        duplicate_profiles = 0
        for user in users:
            profile_count = Profile.objects.filter(user=user).count()
            if profile_count > 1:
                # Keep the first profile and delete the rest
                profiles = Profile.objects.filter(user=user)
                first_profile = profiles.first()
                profiles.exclude(id=first_profile.id).delete()
                duplicate_profiles += 1
        
        self.stdout.write(self.style.SUCCESS(f'Fixed {duplicate_profiles} users with duplicate profiles')) 