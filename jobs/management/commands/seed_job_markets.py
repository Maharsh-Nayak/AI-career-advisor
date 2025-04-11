from django.core.management.base import BaseCommand
from jobs.models import JobMarket

class Command(BaseCommand):
    help = 'Seeds the database with sample job market data'

    def handle(self, *args, **options):
        # Sample job markets with required skills
        job_markets = [
            {
                'title': 'Frontend Developer',
                'required_skills': ['html', 'css', 'javascript', 'react', 'typescript', 'git']
            },
            {
                'title': 'Backend Developer',
                'required_skills': ['python', 'django', 'sql', 'rest', 'git', 'docker']
            },
            {
                'title': 'Data Scientist',
                'required_skills': ['python', 'machine learning', 'statistics', 'pandas', 'numpy', 'sql']
            },
            {
                'title': 'DevOps Engineer',
                'required_skills': ['docker', 'kubernetes', 'aws', 'ci/cd', 'linux', 'git']
            },
            {
                'title': 'Full Stack Developer',
                'required_skills': ['javascript', 'python', 'react', 'django', 'sql', 'git']
            }
        ]

        # Create job markets
        for market in job_markets:
            JobMarket.objects.get_or_create(
                title=market['title'],
                defaults={'required_skills': market['required_skills']}
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded job market data')) 