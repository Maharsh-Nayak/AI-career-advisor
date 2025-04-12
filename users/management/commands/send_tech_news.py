from django.core.management.base import BaseCommand
from django.utils import timezone
from users.services import TechNewsService
from users.email_service import TechNewsEmailService
import logging
import time

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fetches technology news and sends email updates to subscribed users'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days', 
            type=int, 
            default=7,
            help='Number of days to look back for news'
        )
        parser.add_argument(
            '--min-articles', 
            type=int, 
            default=1,
            help='Minimum number of articles required to send an email'
        )
        parser.add_argument(
            '--fetch-only', 
            action='store_true',
            help='Only fetch and store articles without sending emails'
        )
        parser.add_argument(
            '--send-only', 
            action='store_true',
            help='Only send emails using already fetched articles'
        )
    
    def handle(self, *args, **options):
        start_time = time.time()
        days = options['days']
        min_articles = options['min_articles']
        fetch_only = options['fetch_only']
        send_only = options['send_only']
        
        self.stdout.write(self.style.SUCCESS(f'Starting tech news update process at {timezone.now()}'))
        
        if not send_only:
            # Fetch and save news for all subscriptions
            self.stdout.write('Fetching technology news from sources...')
            fetch_results = TechNewsService.fetch_and_save_news_for_all_subscriptions()
            
            # Display results
            self.stdout.write(self.style.SUCCESS('News fetching completed:'))
            for tech, count in fetch_results.items():
                self.stdout.write(f'  - {tech}: {count} new articles')
        
        if not fetch_only:
            # Send emails
            self.stdout.write('Sending news digest emails to users...')
            email_results = TechNewsEmailService.send_digest_emails(days=days, min_articles=min_articles)
            
            # Display results
            self.stdout.write(self.style.SUCCESS('Email sending completed:'))
            self.stdout.write(f'  - Total users: {email_results["total_users"]}')
            self.stdout.write(f'  - Successful emails: {email_results["success"]}')
            self.stdout.write(f'  - Failed emails: {email_results["fail"]}')
            self.stdout.write(f'  - Skipped (not enough articles): {email_results["skipped"]}')
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f'Process completed in {elapsed_time:.2f} seconds')) 