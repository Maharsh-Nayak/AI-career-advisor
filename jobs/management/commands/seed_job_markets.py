from django.core.management.base import BaseCommand
from jobs.models import JobMarket

class Command(BaseCommand):
    help = 'Seeds the database with initial job market data'

    def handle(self, *args, **kwargs):
        # Clear existing job markets
        JobMarket.objects.all().delete()

        # Define job markets with their required skills
        job_markets = [
            {
                'title': 'Full Stack Developer',
                'required_skills': [
                    'python', 'javascript', 'html', 'css', 'react', 'django',
                    'sql', 'git', 'docker'
                ]
            },
            {
                'title': 'Data Scientist',
                'required_skills': [
                    'python', 'machine learning', 'data science', 'sql',
                    'tensorflow', 'pytorch', 'statistics', 'numpy', 'pandas'
                ]
            },
            {
                'title': 'DevOps Engineer',
                'required_skills': [
                    'docker', 'kubernetes', 'aws', 'terraform', 'jenkins',
                    'git', 'python', 'linux', 'ci/cd'
                ]
            },
            {
                'title': 'Frontend Developer',
                'required_skills': [
                    'javascript', 'typescript', 'react', 'html', 'css',
                    'vue', 'angular', 'git', 'webpack'
                ]
            },
            {
                'title': 'Backend Developer',
                'required_skills': [
                    'python', 'java', 'sql', 'nosql', 'django', 'spring',
                    'docker', 'git', 'api design'
                ]
            },
            {
                'title': 'Machine Learning Engineer',
                'required_skills': [
                    'python', 'machine learning', 'deep learning', 'tensorflow',
                    'pytorch', 'nlp', 'computer vision', 'statistics'
                ]
            }
        ]

        # Create job markets
        for job_market in job_markets:
            JobMarket.objects.create(
                title=job_market['title'],
                required_skills=job_market['required_skills']
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded job markets')) 