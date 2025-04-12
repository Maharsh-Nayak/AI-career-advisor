import requests
import datetime
from django.utils import timezone
from .models import NewsArticle, TechNewsSubscription

class TechNewsService:
    """Service for fetching technology news from various sources"""
    
    @staticmethod
    def fetch_news_for_technology(technology, limit=5):
        """
        Fetch news for a specific technology
        
        Args:
            technology (str): The technology to fetch news for
            limit (int): Maximum number of articles to return
            
        Returns:
            list: List of dictionaries containing news data
        """
        # Try multiple news sources, starting with NewsAPI
        try:
            articles = TechNewsService._fetch_from_newsapi(technology, limit)
            if articles:
                return articles
        except Exception as e:
            print(f"Error fetching from NewsAPI: {e}")
        
        # Fallback to HackerNews if NewsAPI fails
        try:
            articles = TechNewsService._fetch_from_hackernews(technology, limit)
            if articles:
                return articles
        except Exception as e:
            print(f"Error fetching from HackerNews: {e}")
        
        # Return mock data if all APIs fail
        return TechNewsService._get_mock_news(technology, limit)
    
    @staticmethod
    def _fetch_from_newsapi(technology, limit=5):
        """Fetch news from NewsAPI.org"""
        # Note: In production, you would use your own API key
        api_key = "YOUR_NEWSAPI_KEY"  # Replace with actual key from environment vars
        url = f"https://newsapi.org/v2/everything?q={technology}+programming+technology&sortBy=publishedAt&pageSize={limit}&apiKey={api_key}"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok' and data.get('articles'):
                return [
                    {
                        'title': article.get('title'),
                        'url': article.get('url'),
                        'source': article.get('source', {}).get('name', 'NewsAPI'),
                        'published_date': article.get('publishedAt'),
                        'technology': technology,
                        'summary': article.get('description', '')[:500]
                    }
                    for article in data['articles'][:limit]
                ]
        return []
    
    @staticmethod
    def _fetch_from_hackernews(technology, limit=5):
        """Fetch technology news from HackerNews"""
        # Search for stories containing the technology keyword
        url = f"https://hn.algolia.com/api/v1/search?query={technology}&tags=story&numericFilters=created_at_i>1612137600"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'hits' in data:
                return [
                    {
                        'title': hit.get('title'),
                        'url': hit.get('url', f"https://news.ycombinator.com/item?id={hit.get('objectID')}"),
                        'source': 'HackerNews',
                        'published_date': datetime.datetime.fromtimestamp(hit.get('created_at_i'), tz=timezone.utc).isoformat(),
                        'technology': technology,
                        'summary': hit.get('story_text', '')[:500] if hit.get('story_text') else 'No summary available'
                    }
                    for hit in data['hits'][:limit] if hit.get('title')
                ]
        return []
    
    @staticmethod
    def _get_mock_news(technology, limit=3):
        """Generate mock news data when APIs fail"""
        current_time = timezone.now()
        
        return [
            {
                'title': f"Latest {technology.title()} Developments: What You Need to Know",
                'url': f"https://example.com/tech/{technology}",
                'source': 'Tech Trends (Mock)',
                'published_date': current_time.isoformat(),
                'technology': technology,
                'summary': f"Recent advances in {technology} are changing the development landscape. Learn how these changes might affect your projects and career path."
            },
            {
                'title': f"How Companies Are Using {technology.title()} in 2023",
                'url': f"https://example.com/industry/{technology}",
                'source': 'Industry Insights (Mock)',
                'published_date': (current_time - datetime.timedelta(days=1)).isoformat(),
                'technology': technology,
                'summary': f"Major companies are implementing {technology} in innovative ways. This article explores the most effective use cases and implementation strategies."
            },
            {
                'title': f"Learning {technology.title()}: A Comprehensive Guide",
                'url': f"https://example.com/learn/{technology}",
                'source': 'Dev Academy (Mock)',
                'published_date': (current_time - datetime.timedelta(days=2)).isoformat(),
                'technology': technology,
                'summary': f"Whether you're just starting with {technology} or looking to deepen your expertise, this guide covers all the essential concepts and practical applications."
            }
        ][:limit]
    
    @staticmethod
    def save_articles_to_db(articles):
        """Save fetched articles to the database"""
        saved_articles = []
        for article_data in articles:
            # Convert ISO format string to datetime object if necessary
            if isinstance(article_data['published_date'], str):
                try:
                    article_data['published_date'] = datetime.datetime.fromisoformat(article_data['published_date'].replace('Z', '+00:00'))
                except ValueError:
                    # If parsing fails, use current time
                    article_data['published_date'] = timezone.now()
            
            # Check if article with same title and URL already exists
            existing = NewsArticle.objects.filter(
                title=article_data['title'],
                url=article_data['url']
            ).first()
            
            if not existing:
                article = NewsArticle.objects.create(**article_data)
                saved_articles.append(article)
        
        return saved_articles
    
    @staticmethod
    def fetch_and_save_news_for_all_subscriptions():
        """Fetch and save news for all technology subscriptions"""
        # Get distinct technologies from subscriptions
        technologies = TechNewsSubscription.objects.values_list('technology', flat=True).distinct()
        
        results = {}
        for tech in technologies:
            articles = TechNewsService.fetch_news_for_technology(tech)
            saved = TechNewsService.save_articles_to_db(articles)
            results[tech] = len(saved)
        
        return results
    
    @staticmethod
    def get_news_for_user(user, days=7, limit=10):
        """Get recent news articles relevant to a user's subscribed technologies"""
        # Get user's subscribed technologies
        subscriptions = TechNewsSubscription.objects.filter(user=user)
        technologies = [sub.technology for sub in subscriptions]
        
        if not technologies:
            return []
        
        # Get recent articles for these technologies
        since_date = timezone.now() - datetime.timedelta(days=days)
        articles = NewsArticle.objects.filter(
            technology__in=technologies,
            published_date__gte=since_date
        ).order_by('-published_date')[:limit]
        
        return articles 