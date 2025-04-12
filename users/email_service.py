from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from .models import TechNewsSubscription, NewsArticle, Profile
from .services import TechNewsService
import datetime
import logging

logger = logging.getLogger(__name__)

class TechNewsEmailService:
    """Service for sending technology news emails to users"""
    
    @staticmethod
    def send_tech_news_email(user, articles):
        """
        Send a technology news email to a specific user
        
        Args:
            user (User): The user to send the email to
            articles (list): List of NewsArticle objects to include in the email
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not articles:
            return False
            
        try:
            # Get user email
            to_email = user.email
            if not to_email:
                logger.warning(f"User {user.username} has no email address")
                return False
                
            # Group articles by technology
            articles_by_tech = {}
            for article in articles:
                tech = article.technology
                if tech not in articles_by_tech:
                    articles_by_tech[tech] = []
                articles_by_tech[tech].append(article)
            
            # Create context for the email template
            context = {
                'username': user.username,
                'articles_by_tech': articles_by_tech,
                'total_articles': len(articles),
                'date': timezone.now().strftime('%B %d, %Y')
            }
            
            # Render HTML email
            html_content = render_to_string('emails/tech_news_update.html', context)
            text_content = strip_tags(html_content)
            
            # Create the email
            subject = f"Tech News Update: {len(articles)} New Articles About Your Skills"
            from_email = settings.DEFAULT_FROM_EMAIL
            
            # Send the email as both HTML and plain text
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            # Update last_notified timestamp for user's subscriptions
            technologies = list(articles_by_tech.keys())
            TechNewsSubscription.objects.filter(
                user=user,
                technology__in=technologies
            ).update(last_notified=timezone.now())
            
            return True
        
        except Exception as e:
            logger.error(f"Error sending tech news email to {user.username}: {str(e)}")
            return False
    
    @staticmethod
    def send_digest_emails(days=7, min_articles=1):
        """
        Send digest emails to all users who have opted in
        
        Args:
            days (int): Number of days to look back for news
            min_articles (int): Minimum number of articles required to send an email
            
        Returns:
            dict: Results with counts of successful and failed emails
        """
        results = {
            'success': 0,
            'fail': 0,
            'skipped': 0,
            'total_users': 0
        }
        
        # Get all users who have opted in to receive news
        users_with_skills = User.objects.filter(
            profile__receive_news_updates=True,
            profile__skills__isnull=False
        ).exclude(profile__skills="").exclude(email="")
        
        results['total_users'] = users_with_skills.count()
        
        # Process each user
        for user in users_with_skills:
            # Get news articles for this user
            articles = TechNewsService.get_news_for_user(user, days=days)
            
            if len(articles) >= min_articles:
                sent = TechNewsEmailService.send_tech_news_email(user, articles)
                if sent:
                    results['success'] += 1
                else:
                    results['fail'] += 1
            else:
                results['skipped'] += 1
        
        return results
    
    @staticmethod
    def send_welcome_tech_email(user):
        """
        Send a welcome email with initial technology news
        
        Args:
            user (User): The new user to send the welcome email to
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Get user skills
            profile = user.profile
            skills = profile.get_skills_list()
            
            if not skills or not user.email:
                return False
            
            # Get some initial articles based on user's top skills (up to 3)
            articles = []
            for skill in skills[:3]:
                # Fetch news for this skill
                skill_articles = TechNewsService.fetch_news_for_technology(skill, limit=2)
                # Save and get article objects
                saved_articles = TechNewsService.save_articles_to_db(skill_articles)
                articles.extend(saved_articles)
            
            if articles:
                # Send the email
                return TechNewsEmailService.send_tech_news_email(user, articles)
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending welcome tech email to {user.username}: {str(e)}")
            return False 