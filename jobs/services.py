import requests
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor
from .models import JobListing

class JobFetcher:
    @staticmethod
    def fetch_remotive_jobs(keyword):
        """Fetch jobs from Remotive API"""
        api_url = f"https://remotive.com/api/remote-jobs?search={quote_plus(keyword)}&limit=5"
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'jobs' in data and isinstance(data['jobs'], list):
                return [{
                    'title': job.get('title', 'N/A'),
                    'company_name': job.get('company_name', 'N/A'),
                    'url': job.get('url', '#'),
                    'source': 'Remotive',
                    'location': 'Remote'
                } for job in data['jobs'][:5]]
            return []
        except Exception as e:
            print(f"Remotive API request failed: {e}")
            return []

    @staticmethod
    def fetch_adzuna_jobs(keyword):
        """Fetch jobs from Adzuna API"""
        app_id = "7429e9ca"
        app_key = "5f2692c344ec934b9691b59d6ae1352a"
        api_url = f"https://api.adzuna.com/v1/api/jobs/gb/search/1?app_id={app_id}&app_key={app_key}&results_per_page=5&what={quote_plus(keyword)}"
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'results' in data:
                return [{
                    'title': job.get('title', 'N/A'),
                    'company_name': job.get('company', {}).get('display_name', 'N/A'),
                    'url': job.get('redirect_url', '#'),
                    'source': 'Adzuna',
                    'location': job.get('location', {}).get('display_name', 'N/A')
                } for job in data['results'][:5]]
            return []
        except Exception as e:
            print(f"Adzuna API request failed: {e}")
            return []

    @staticmethod
    def fetch_jsearch_jobs(keyword):
        """Fetch jobs from JSearch API"""
        api_url = f"https://jsearch.p.rapidapi.com/search?query={quote_plus(keyword)}&page=1&num_pages=1"
        headers = {
            "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        try:
            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'data' in data:
                return [{
                    'title': job.get('job_title', 'N/A'),
                    'company_name': job.get('employer_name', 'N/A'),
                    'url': job.get('job_apply_link', '#'),
                    'source': 'JSearch',
                    'location': job.get('job_city', 'N/A')
                } for job in data['data'][:5]]
            return []
        except Exception as e:
            print(f"JSearch API request failed: {e}")
            return []

    @classmethod
    def fetch_all_jobs(cls, keyword):
        """Fetch jobs from all APIs concurrently"""
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(cls.fetch_remotive_jobs, keyword),
                executor.submit(cls.fetch_adzuna_jobs, keyword),
                executor.submit(cls.fetch_jsearch_jobs, keyword)
            ]
            
            all_jobs = []
            for future in futures:
                try:
                    jobs = future.result()
                    all_jobs.extend(jobs)
                except Exception as e:
                    print(f"Error fetching jobs: {e}")
            
            # Remove duplicates based on title and company
            seen = set()
            unique_jobs = []
            for job in all_jobs:
                key = (job['title'], job['company_name'])
                if key not in seen:
                    seen.add(key)
                    unique_jobs.append(job)
            
            return unique_jobs 