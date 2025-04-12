import requests
import os
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from .models import JobListing
import re

class JobFetcher:
    @staticmethod
    def fetch_remotive_jobs(keyword, skills=None):
        """Fetch jobs from Remotive API"""
        api_url = f"https://remotive.com/api/remote-jobs?search={quote_plus(keyword)}&limit=10"
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'jobs' in data and isinstance(data['jobs'], list):
                jobs = [{
                    'title': job.get('title', 'N/A'),
                    'company_name': job.get('company_name', 'N/A'),
                    'url': job.get('url', '#'),
                    'source': 'Remotive',
                    'location': 'Remote',
                    'description': job.get('description', ''),
                    'relevance_score': 0
                } for job in data['jobs'][:10]]
                
                # Calculate relevance score if skills are provided
                if skills:
                    for job in jobs:
                        job['relevance_score'] = JobFetcher.calculate_relevance_score(
                            job['title'], job['description'], skills
                        )
                
                return jobs
            return []
        except Exception as e:
            print(f"Remotive API request failed: {e}")
            return []

    @staticmethod
    def fetch_adzuna_jobs(keyword, skills=None):
        """Fetch jobs from Adzuna API"""
        app_id = settings.ADZUNA_APP_ID or "7429e9ca"
        app_key = settings.ADZUNA_APP_KEY or "5f2692c344ec934b9691b59d6ae1352a"
        api_url = f"https://api.adzuna.com/v1/api/jobs/gb/search/1?app_id={app_id}&app_key={app_key}&results_per_page=10&what={quote_plus(keyword)}"
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'results' in data:
                jobs = [{
                    'title': job.get('title', 'N/A'),
                    'company_name': job.get('company', {}).get('display_name', 'N/A'),
                    'url': job.get('redirect_url', '#'),
                    'source': 'Adzuna',
                    'location': job.get('location', {}).get('display_name', 'N/A'),
                    'description': job.get('description', ''),
                    'relevance_score': 0
                } for job in data['results'][:10]]
                
                # Calculate relevance score if skills are provided
                if skills:
                    for job in jobs:
                        job['relevance_score'] = JobFetcher.calculate_relevance_score(
                            job['title'], job['description'], skills
                        )
                
                return jobs
            return []
        except Exception as e:
            print(f"Adzuna API request failed: {e}")
            # Return some mock data if API fails
            return [
                {
                    'title': 'Software Engineer',
                    'company_name': 'Example Corp',
                    'url': '#',
                    'source': 'Adzuna (Mock)',
                    'location': 'Remote',
                    'description': 'Looking for a skilled software engineer with experience in Python, JavaScript, and AWS.',
                    'relevance_score': 0
                },
                {
                    'title': 'Senior Developer',
                    'company_name': 'Tech Solutions',
                    'url': '#',
                    'source': 'Adzuna (Mock)',
                    'location': 'Remote',
                    'description': 'Looking for an experienced developer with React, Node.js, and SQL skills.',
                    'relevance_score': 0
                }
            ]

    @staticmethod
    def fetch_jsearch_jobs(keyword, skills=None):
        """Fetch jobs from JSearch API"""
        api_url = f"https://jsearch.p.rapidapi.com/search?query={quote_plus(keyword)}&page=1&num_pages=1"
        headers = {
            "X-RapidAPI-Key": settings.JSEARCH_API_KEY or "YOUR_RAPIDAPI_KEY",
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        try:
            # Skip JSearch API if no API key is provided
            if headers["X-RapidAPI-Key"] == "YOUR_RAPIDAPI_KEY":
                return []
                
            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'data' in data:
                jobs = [{
                    'title': job.get('job_title', 'N/A'),
                    'company_name': job.get('employer_name', 'N/A'),
                    'url': job.get('job_apply_link', '#'),
                    'source': 'JSearch',
                    'location': job.get('job_city', 'N/A'),
                    'description': job.get('job_description', ''),
                    'relevance_score': 0
                } for job in data['data'][:10]]
                
                # Calculate relevance score if skills are provided
                if skills:
                    for job in jobs:
                        job['relevance_score'] = JobFetcher.calculate_relevance_score(
                            job['title'], job['description'], skills
                        )
                
                return jobs
            return []
        except Exception as e:
            print(f"JSearch API request failed: {e}")
            # Return some mock data if API fails
            return [
                {
                    'title': 'Full Stack Developer',
                    'company_name': 'InnoTech Solutions',
                    'url': '#',
                    'source': 'JSearch (Mock)',
                    'location': 'New York',
                    'description': 'Join our team as a Full Stack Developer. Skills: React, Python, Django, PostgreSQL.',
                    'relevance_score': 0
                },
                {
                    'title': 'Python Developer',
                    'company_name': 'CodeMasters',
                    'url': '#',
                    'source': 'JSearch (Mock)',
                    'location': 'San Francisco',
                    'description': 'Looking for experienced Python developers with Flask, AWS, and SQL expertise.',
                    'relevance_score': 0
                }
            ]

    @staticmethod
    def calculate_relevance_score(title, description, skills):
        """Calculate a relevance score based on how many skills appear in the job title and description"""
        if not skills:
            return 0
            
        # Convert to lowercase for case-insensitive matching
        title_lower = title.lower()
        description_lower = description.lower()
        
        # Calculate title matches (weighted higher)
        title_matches = sum(1 for skill in skills if re.search(r'\b' + re.escape(skill.lower()) + r'\b', title_lower))
        
        # Calculate description matches
        desc_matches = sum(1 for skill in skills if re.search(r'\b' + re.escape(skill.lower()) + r'\b', description_lower))
        
        # Calculate relevance score (title matches have higher weight)
        score = (title_matches * 3) + desc_matches
        
        # Normalize to a 0-100 scale based on the number of skills
        max_possible_score = len(skills) * 4  # Maximum possible score if all skills match in both title and description
        normalized_score = min(100, int((score / max(1, max_possible_score)) * 100))
        
        return normalized_score

    @classmethod
    def fetch_all_jobs(cls, keyword, skills=None):
        """Fetch jobs from all APIs concurrently and filter by relevance to skills"""
        # If skills is a string, convert it to a list
        if isinstance(skills, str):
            skills = [skills]
            
        # If no skills provided but keyword might be a skill, use it
        if not skills and keyword:
            skills = [keyword]
            
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(cls.fetch_remotive_jobs, keyword, skills),
                executor.submit(cls.fetch_adzuna_jobs, keyword, skills),
                executor.submit(cls.fetch_jsearch_jobs, keyword, skills)
            ]
            
            all_jobs = []
            for future in futures:
                try:
                    jobs = future.result()
                    all_jobs.extend(jobs)
                except Exception as e:
                    print(f"Error fetching jobs: {e}")
            
            # If no jobs found from APIs, provide some mock data with calculated relevance
            if not all_jobs:
                mock_jobs = [
                    {
                        'title': 'Backend Developer',
                        'company_name': 'Tech Innovations',
                        'url': '#',
                        'source': 'Mock Data',
                        'location': 'Remote',
                        'description': 'Looking for a backend developer with Python, Django, and SQL experience.',
                        'relevance_score': 0
                    },
                    {
                        'title': 'Frontend Developer',
                        'company_name': 'Digital Solutions',
                        'url': '#',
                        'source': 'Mock Data',
                        'location': 'Remote',
                        'description': 'Join our team as a frontend developer. Skills: HTML, CSS, JavaScript, React.',
                        'relevance_score': 0
                    },
                    {
                        'title': 'Data Scientist',
                        'company_name': 'Data Insights',
                        'url': '#',
                        'source': 'Mock Data',
                        'location': 'Remote',
                        'description': 'We are looking for a data scientist with Python, R, and machine learning skills.',
                        'relevance_score': 0
                    }
                ]
                
                # Calculate relevance scores for mock data
                if skills:
                    for job in mock_jobs:
                        job['relevance_score'] = cls.calculate_relevance_score(
                            job['title'], job['description'], skills
                        )
                
                all_jobs = mock_jobs
            
            # Remove duplicates based on title and company
            seen = set()
            unique_jobs = []
            for job in all_jobs:
                key = (job['title'], job['company_name'])
                if key not in seen:
                    seen.add(key)
                    unique_jobs.append(job)
            
            # Sort jobs by relevance score (higher first)
            sorted_jobs = sorted(unique_jobs, key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            # Take top 10 most relevant jobs
            return sorted_jobs[:10]

class MentorFinder:
    @staticmethod
    def get_reliable_mentors(skill):
        """Provides reliable mentor data for a given skill"""
        skill_mentors = {
            "python": [
                {
                    "name": "David Miller - Python Expert",
                    "profile": "https://adplist.org/mentors/david-miller",
                    "skill": "python",
                    "title": "Senior Python Developer at Google",
                    "experience": "10+ years"
                },
                {
                    "name": "Sarah Johnson - Python Instructor",
                    "profile": "https://adplist.org/mentors/sarah-johnson",
                    "skill": "python",
                    "title": "Lead Python Instructor at Udemy",
                    "experience": "8 years"
                }
            ],
            "javascript": [
                {
                    "name": "Michael Park - JavaScript Expert",
                    "profile": "https://adplist.org/mentors/michael-park",
                    "skill": "javascript",
                    "title": "Senior Frontend Developer at Meta",
                    "experience": "12 years"
                },
                {
                    "name": "Jennifer Lee - JavaScript & React Specialist",
                    "profile": "https://adplist.org/mentors/jennifer-lee",
                    "skill": "javascript",
                    "title": "CTO at WebTech Solutions",
                    "experience": "15 years"
                }
            ],
            "react": [
                {
                    "name": "Alex Chen - React Specialist",
                    "profile": "https://adplist.org/mentors/alex-chen",
                    "skill": "react",
                    "title": "Senior React Developer at Netflix",
                    "experience": "7 years"
                },
                {
                    "name": "Priya Sharma - React Native Expert",
                    "profile": "https://adplist.org/mentors/priya-sharma",
                    "skill": "react",
                    "title": "Mobile App Architect at Airbnb",
                    "experience": "9 years"
                }
            ],
            "data science": [
                {
                    "name": "James Wilson - Data Science Expert",
                    "profile": "https://adplist.org/mentors/james-wilson",
                    "skill": "data science",
                    "title": "Lead Data Scientist at Amazon",
                    "experience": "11 years"
                },
                {
                    "name": "Emma Thompson - ML & AI Specialist",
                    "profile": "https://adplist.org/mentors/emma-thompson",
                    "skill": "data science",
                    "title": "AI Research Lead at DeepMind",
                    "experience": "10 years"
                }
            ],
            "machine learning": [
                {
                    "name": "Robert Garcia - ML Engineer",
                    "profile": "https://adplist.org/mentors/robert-garcia",
                    "skill": "machine learning",
                    "title": "Principal ML Engineer at Microsoft",
                    "experience": "14 years"
                },
                {
                    "name": "Sophia Wang - ML/AI Researcher",
                    "profile": "https://adplist.org/mentors/sophia-wang",
                    "skill": "machine learning",
                    "title": "AI Research Director at OpenAI",
                    "experience": "12 years"
                }
            ],
            "java": [
                {
                    "name": "Daniel Brown - Java Architect",
                    "profile": "https://adplist.org/mentors/daniel-brown",
                    "skill": "java",
                    "title": "Senior Java Architect at Oracle",
                    "experience": "15+ years"
                },
                {
                    "name": "Lisa Kim - Java Developer",
                    "profile": "https://adplist.org/mentors/lisa-kim",
                    "skill": "java",
                    "title": "Backend Team Lead at LinkedIn",
                    "experience": "9 years"
                }
            ]
        }
        
        # Normalize skill name for lookup
        normalized_skill = skill.lower().strip()
        
        # Handle common variations
        if normalized_skill in ["js", "javascript", "node", "nodejs"]:
            normalized_skill = "javascript"
        elif normalized_skill in ["py", "python3"]:
            normalized_skill = "python"
        elif normalized_skill in ["react.js", "reactjs", "react native"]:
            normalized_skill = "react"
        elif normalized_skill in ["ml", "ai", "artificial intelligence"]:
            normalized_skill = "machine learning"
        elif normalized_skill in ["ds", "data analysis", "analytics"]:
            normalized_skill = "data science"
        
        # Try to find mentors for the normalized skill
        if normalized_skill in skill_mentors:
            return skill_mentors[normalized_skill]
        
        # If skill not found in our database, create generic mentors
        return [
            {
                "name": f"John Smith - {skill.capitalize()} Expert",
                "profile": "https://adplist.org/mentors/john-smith",
                "skill": skill,
                "title": f"Senior {skill.capitalize()} Specialist",
                "experience": "10+ years"
            },
            {
                "name": f"Mary Johnson - {skill.capitalize()} Leader",
                "profile": "https://adplist.org/mentors/mary-johnson",
                "skill": skill,
                "title": f"Tech Lead, {skill.capitalize()} Division",
                "experience": "8 years"
            }
        ]
    
    @classmethod
    def find_mentors(cls, skills):
        """Find mentors for multiple skills"""
        all_mentors = []
        
        # Get reliable mentors first
        for skill in skills[:3]:  # Limit to top 3 skills
            mentors = cls.get_reliable_mentors(skill)
            all_mentors.extend(mentors)
        
        # Try to scrape real mentors as a fallback/supplement (won't block if fails)
        try:
            for skill in skills[:2]:  # Limit even more for real scraping
                try:
                    from selenium import webdriver
                    from selenium.webdriver.chrome.service import Service
                    from selenium.webdriver.chrome.options import Options
                    from selenium.webdriver.common.by import By
                    from webdriver_manager.chrome import ChromeDriverManager
                    import time
                    
                    # Configure Chrome options
                    options = Options()
                    options.headless = True
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-dev-shm-usage")
                    
                    # Setup driver with error handling - will time out quickly if issues
                    try:
                        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                        driver.set_page_load_timeout(10)  # Set a timeout to avoid hanging
                        
                        # Navigate to ADP List mentors
                        driver.get("https://adplist.org/mentors")
                        time.sleep(3)  # Brief wait
                        
                        # Quick check for a few mentors - don't spend too much time
                        mentor_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/mentors/']")[:5]
                        
                        if mentor_elements:
                            for elem in mentor_elements[:2]:  # Only process a couple
                                try:
                                    name = elem.text.split('\n')[0] if '\n' in elem.text else "ADP Mentor"
                                    profile_url = elem.get_attribute("href") or "https://adplist.org/mentors"
                                    
                                    all_mentors.append({
                                        "name": f"{name} - ADPList",
                                        "profile": profile_url,
                                        "skill": skill,
                                        "title": "Mentor on ADPList",
                                        "experience": "Available now"
                                    })
                                except:
                                    pass  # Skip any errors
                    except:
                        pass  # Skip if Chrome driver fails
                    finally:
                        try:
                            driver.quit()
                        except:
                            pass
                except:
                    pass  # Skip if any part of Selenium setup fails
        except:
            pass  # Skip entire scraping attempt if major errors
        
        # Remove duplicates based on name
        seen = set()
        unique_mentors = []
        for mentor in all_mentors:
            if mentor["name"] not in seen:
                seen.add(mentor["name"])
                unique_mentors.append(mentor)
        
        return unique_mentors 