"""
Fallback utilities for when spaCy is not available.
This module provides simple implementations that don't require spaCy.
"""
import re
import random
import json
from django.conf import settings
from datetime import datetime, timedelta

def fallback_extract_keywords(text):
    """
    Extract keywords from text without using spaCy
    This is a more sophisticated fallback that uses regex patterns
    """
    # Normalize text
    text = text.lower()
    
    # Define patterns for common technical terms and job titles
    patterns = {
        'job_titles': r'(senior|junior|lead|principal|staff)?\s?(software|web|mobile|frontend|backend|fullstack|devops|cloud|data|machine learning|ai|ml|systems|network|security|database|qa|test)\s?(engineer|developer|architect|administrator|analyst|scientist|designer|specialist|manager|director|lead)',
        'technologies': r'\b(python|java|javascript|typescript|c\+\+|c#|php|go|rust|ruby|swift|kotlin|react|angular|vue|node\.js|express|django|flask|spring|laravel|aws|azure|gcp|docker|kubernetes|terraform|jenkins|git|sql|nosql|mongodb|postgresql|mysql|oracle|redis)\b',
        'skills': r'\b(agile|scrum|kanban|ci\/cd|tdd|rest|graphql|microservices|serverless|cloud native|distributed systems|algorithms|data structures|design patterns|oop|functional programming|testing|debugging|deployment|monitoring|security|performance)\b',
        'domains': r'\b(fintech|healthtech|edtech|e-commerce|saas|enterprise|b2b|b2c|gaming|social media|cybersecurity|blockchain|iot|ar\/vr|mobile apps|web applications)\b'
    }
    
    keywords = []
    
    # Extract using patterns
    for pattern_type, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if pattern_type == 'job_titles':
            # Handle job title tuples
            for match in matches:
                job_title = ' '.join([part for part in match if part]).strip()
                if job_title and job_title not in keywords:
                    keywords.append(job_title)
        else:
            # Handle simple string matches
            for match in matches:
                if match and match not in keywords:
                    keywords.append(match)
    
    # Extract noun phrases using a simple approach (words between stop words)
    stop_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'can', 'could', 'shall', 'should', 'will', 'would', 'may', 'might', 'must', 'in', 'of', 'with', 'about', 'between', 'through'}
    
    # Split by stop words
    words = []
    current_phrase = []
    
    for word in re.findall(r'\b\w+\b', text):
        if word in stop_words:
            if current_phrase:
                words.append(' '.join(current_phrase))
                current_phrase = []
        else:
            current_phrase.append(word)
    
    if current_phrase:
        words.append(' '.join(current_phrase))
    
    # Add multi-word phrases that might be meaningful
    for phrase in words:
        if len(phrase.split()) > 1 and phrase not in keywords:
            keywords.append(phrase)
    
    # Add single words that might be important (longer than 3 characters)
    for word in re.findall(r'\b\w{4,}\b', text):
        if word not in stop_words and word not in keywords:
            keywords.append(word)
    
    return list(set(keywords))

def fallback_match_suggestions(user_skills, job_skills):
    """Match user skills with job skills without spaCy, using string similarity"""
    # Direct matches
    common_skills = set([skill.lower() for skill in user_skills]) & set([skill.lower() for skill in job_skills])
    
    # Find partial matches
    partial_matches = []
    for user_skill in user_skills:
        user_skill_lower = user_skill.lower()
        for job_skill in job_skills:
            job_skill_lower = job_skill.lower()
            
            # Skip exact matches
            if user_skill_lower == job_skill_lower:
                continue
                
            # Check if one contains the other
            if user_skill_lower in job_skill_lower or job_skill_lower in user_skill_lower:
                partial_matches.append(user_skill)
                break
                
            # Check word overlap for multi-word skills
            user_words = set(user_skill_lower.split())
            job_words = set(job_skill_lower.split())
            
            # If significant overlap (more than half the words match)
            if len(user_words & job_words) >= min(len(user_words), len(job_words)) / 2:
                partial_matches.append(user_skill)
                break
    
    # Convert common_skills back to original cases from user_skills
    result = [skill for skill in user_skills if skill.lower() in common_skills]
    
    # Add partial matches that aren't already included
    for skill in partial_matches:
        if skill not in result:
            result.append(skill)
    
    return result

def generate_linkedin_search_url(job_title, location=None):
    """Generate a LinkedIn search URL for networking"""
    base_url = "https://www.linkedin.com/search/results/people/"
    params = []
    
    if job_title:
        # Replace spaces with %20 for URL encoding
        job_title = job_title.replace(' ', '%20')
        params.append(f"keywords={job_title}")
    
    if location:
        # Replace spaces with %20 for URL encoding
        location = location.replace(' ', '%20')
        params.append(f"location={location}")
    
    # Join params with &
    query_string = "&".join(params)
    
    # Return the final URL
    return f"{base_url}?{query_string}"

def fallback_linkedin_profiles(job_title, industry=None, count=3):
    """Generate mock LinkedIn profiles for networking examples"""
    
    # Define templates for various profile components
    first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Quinn", "Sam", "Jamie", "Avery", 
                   "Cameron", "Blake", "Dakota", "Hayden", "Reese", "Skyler", "Drew", "Jessie", "Parker", "Peyton",
                   "Rowan", "Harley", "Charlie", "Emerson", "Finley", "River", "Phoenix", "Sage", "Shawn", "Tyler"]
    
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Wilson", "Anderson", "Taylor", "Thomas", "Hernandez", "Moore", "Martin", "Jackson", "Thompson", "White",
                  "Lopez", "Lee", "Gonzalez", "Harris", "Clark", "Lewis", "Robinson", "Walker", "Perez", "Hall"]
    
    companies = {
        "tech": ["TechSolutions Inc.", "Innovate AI", "CloudScale Systems", "Data Dynamics", "CodeCraft Technologies", 
                 "Future Technologies", "ByteSphere", "Quantum Computing", "Digital Nexus", "Cyber Defense Systems"],
        "finance": ["Global Financial Group", "FinTech Innovations", "Capital Investment Partners", "Wealth Management Solutions",
                   "Banking Technologies", "Financial Analytics Corp", "Investment Strategies Inc.", "Secure Payment Systems",
                   "Trading Platforms Ltd.", "Financial Security Solutions"],
        "healthcare": ["HealthTech Systems", "Medical Innovations", "Patient Care Technologies", "Healthcare Analytics", 
                      "MedData Solutions", "Clinical Systems Inc.", "Health Management Platforms", "BioTech Research",
                      "Medical Software Solutions", "Digital Health Networks"],
        "education": ["EduTech Innovations", "Learning Systems Inc.", "Educational Software Solutions", "Digital Classroom Technologies",
                     "Academic Analytics", "Smart Learning Platforms", "Knowledge Management Systems", "Educational Research Labs",
                     "Curriculum Technologies", "Virtual Learning Environments"],
        "manufacturing": ["Manufacturing Solutions", "Industrial Technologies", "Production Systems Inc.", "Supply Chain Innovations",
                         "Factory Automation Technologies", "Industrial IoT Systems", "Quality Control Technologies",
                         "Manufacturing Analytics", "Precision Engineering Systems", "Production Optimization Solutions"]
    }
    
    locations = ["San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX", "Boston, MA", 
                 "Chicago, IL", "Los Angeles, CA", "Denver, CO", "Atlanta, GA", "Portland, OR",
                 "Dallas, TX", "San Diego, CA", "Washington, DC", "Philadelphia, PA", "Miami, FL",
                 "Detroit, MI", "Phoenix, AZ", "Minneapolis, MN", "Charlotte, NC", "San Jose, CA",
                 "London, UK", "Toronto, Canada", "Berlin, Germany", "Sydney, Australia", "Singapore"]
    
    universities = ["Stanford University", "MIT", "Carnegie Mellon University", "University of California", "Georgia Tech",
                    "University of Michigan", "University of Washington", "Cornell University", "Princeton University",
                    "University of Texas", "New York University", "Purdue University", "University of Illinois",
                    "University of Wisconsin", "University of Pennsylvania", "Harvard University", "Columbia University",
                    "UC Berkeley", "Caltech", "University of Chicago", "Yale University", "Duke University"]
    
    degrees = ["Bachelor of Science in Computer Science", "Master of Science in Computer Engineering", 
               "PhD in Computer Science", "Bachelor of Engineering", "Master of Information Technology",
               "Bachelor of Science in Data Science", "Master of Business Administration", "Bachelor of Arts in Mathematics",
               "Master of Science in Artificial Intelligence", "Bachelor of Science in Software Engineering",
               "Master of Science in Cybersecurity", "Bachelor of Science in Information Systems"]
    
    skill_sets = {
        "software developer": ["Java", "Python", "JavaScript", "REST APIs", "Git", "SQL", "Object-Oriented Programming", 
                            "Software Architecture", "Agile Development", "Unit Testing", "CI/CD", "Microservices"],
        "web developer": ["HTML", "CSS", "JavaScript", "React", "Node.js", "TypeScript", "Angular", "Vue.js", 
                       "Web APIs", "Responsive Design", "Frontend Development", "Backend Development"],
        "data scientist": ["Python", "R", "SQL", "Machine Learning", "Statistical Analysis", "Data Visualization", 
                         "TensorFlow", "PyTorch", "Big Data", "Data Mining", "Natural Language Processing", "Predictive Modeling"],
        "data engineer": ["SQL", "Python", "ETL", "Data Warehousing", "Hadoop", "Spark", "AWS", "Azure", 
                        "Database Design", "Data Modeling", "Big Data", "Data Pipeline Development"],
        "machine learning engineer": ["Python", "TensorFlow", "PyTorch", "Scikit-learn", "Deep Learning", "Computer Vision", 
                                    "Natural Language Processing", "Feature Engineering", "Model Deployment", "MLOps"],
        "devops engineer": ["AWS", "Docker", "Kubernetes", "Terraform", "Jenkins", "CI/CD", "Linux", "Ansible", 
                          "Infrastructure as Code", "Cloud Architecture", "Monitoring", "Automation"],
        "cloud architect": ["AWS", "Azure", "GCP", "Cloud Architecture", "Infrastructure as Code", "Microservices", 
                           "Serverless", "Container Orchestration", "Network Design", "Security Architecture"],
        "security engineer": ["Network Security", "Penetration Testing", "Security Architecture", "SIEM", "Vulnerability Assessment", 
                            "Incident Response", "Security Compliance", "Encryption", "Access Control", "Security Auditing"],
        "product manager": ["Product Strategy", "User Experience", "Market Research", "Competitive Analysis", "Agile", 
                          "Roadmap Planning", "Product Analytics", "Stakeholder Management", "Product Development Lifecycle"],
        "project manager": ["Project Planning", "Risk Management", "Agile", "Scrum", "Jira", "Stakeholder Management", 
                          "Resource Allocation", "Budget Management", "Project Coordination", "Quality Assurance"]
    }
    
    # Get the appropriate industry or default to tech
    if not industry:
        if any(role in job_title.lower() for role in skill_sets.keys()):
            for role, skills in skill_sets.items():
                if role in job_title.lower():
                    industry = "tech"
                    break
        else:
            industry = "tech"
    
    # Ensure industry is valid for our company list
    if industry not in companies:
        industry = "tech"
    
    # Define summary templates based on job title categories
    summary_templates = [
        "{years_experience}+ years of experience as a {job_title} with expertise in {skills_summary}. Passionate about {passion_area} and committed to {commitment_area}.",
        "Experienced {job_title} with a focus on {skills_summary}. Proven track record of {achievement} across {years_experience} years in the industry.",
        "{job_title} with {years_experience}+ years specializing in {skills_summary}. Demonstrated success in {achievement} and passionate about {passion_area}.",
        "Results-driven {job_title} with expertise in {skills_summary}. {years_experience}+ years of experience delivering {commitment_area}.",
        "Innovative {job_title} with {years_experience} years of experience in {industry} industry. Skilled in {skills_summary} with a strong focus on {commitment_area}."
    ]
    
    # Generate the profiles
    profiles = []
    for _ in range(count):
        # Randomly select components
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        full_name = f"{first_name} {last_name}"
        
        # Job title variations
        prefix = random.choice(["Senior ", "Lead ", "Principal ", "", "Staff ", "Director of "])
        job_title_clean = job_title.lower().replace("senior ", "").replace("lead ", "").replace("principal ", "").strip()
        title = f"{prefix}{job_title_clean.title()}"
        
        company = random.choice(companies[industry])
        location = random.choice(locations)
        
        # Education
        university = random.choice(universities)
        degree = random.choice(degrees)
        
        # Determine appropriate skills based on role or fallback to general tech skills
        role_match = None
        for role in skill_sets:
            if role in job_title.lower():
                role_match = role
                break
        
        skills = skill_sets.get(role_match, ["Technical Problem Solving", "Project Management", "Software Development", 
                                            "Communication", "Teamwork", "Critical Thinking"])
        
        # Randomize a subset of skills (3-5)
        skill_count = random.randint(3, min(5, len(skills)))
        selected_skills = random.sample(skills, skill_count)
        
        # Generate summary
        years_experience = random.randint(3, 15)
        skills_summary = ", ".join(random.sample(selected_skills, min(3, len(selected_skills))))
        passion_areas = ["developing scalable solutions", "leveraging cutting-edge technologies", "solving complex technical problems", 
                         "optimizing performance", "improving user experience", "building robust systems"]
        commitment_areas = ["delivering high-quality results", "continuous improvement", "innovation", "best practices", 
                           "collaborative problem solving", "technical excellence"]
        achievements = ["delivering successful projects", "optimizing system performance", "leading cross-functional teams", 
                       "implementing innovative solutions", "reducing costs while improving quality", "exceeding client expectations"]
        
        summary_template = random.choice(summary_templates)
        summary = summary_template.format(
            years_experience=years_experience,
            job_title=job_title,
            skills_summary=skills_summary,
            passion_area=random.choice(passion_areas),
            commitment_area=random.choice(commitment_areas),
            achievement=random.choice(achievements),
            industry=industry
        )
        
        # Create education with realistic dates
        graduation_year = datetime.now().year - years_experience - random.randint(0, 3)
        education = f"{degree} - {university}, {graduation_year}"
        
        # Generate a mock LinkedIn URL
        linkedin_url = f"https://www.linkedin.com/in/{first_name.lower()}-{last_name.lower()}-{random.randint(100, 999)}"
        
        # Assemble the profile
        profile = {
            "name": full_name,
            "title": title,
            "company": company,
            "location": location,
            "summary": summary,
            "skills": selected_skills,
            "education": education,
            "linkedin_url": linkedin_url
        }
        
        profiles.append(profile)
    
    return profiles

def generate_linkedin_profiles_with_gemini(job_title, industry=None, count=3):
    """Generate simulated LinkedIn profiles using Gemini API or fallback to mock data"""
    try:
        # Try using Gemini API
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != 'AIzaSyCphmUSSXd-TpUbu2q2pBJTV9bsV1wmM4Q':
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            prompt = f"""
            Generate {count} simulated LinkedIn profiles for professionals in the {job_title} role
            {f'in the {industry} industry' if industry else ''}.
            
            For each profile, include:
            1. Full name
            2. Current position and company
            3. Location
            4. A brief summary of their experience
            5. Top 3-5 skills
            6. Education background
            
            Format the response as a JSON array with objects that have the following fields:
            - name
            - title
            - company
            - location
            - summary
            - skills (as an array)
            - education
            - linkedin_url (this should be a simulated URL)
            """
            
            response = model.generate_content(prompt)
            text = response.text
            
            # Extract JSON from response
            if "```json" in text:
                json_text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                json_text = text.split("```")[1].strip()
            else:
                json_text = text.strip()
                
            try:
                profiles = json.loads(json_text)
                return profiles
            except:
                # If JSON parsing fails, fall back to mock data
                return fallback_linkedin_profiles(job_title, industry, count)
        else:
            # No valid API key, use mock data
            return fallback_linkedin_profiles(job_title, industry, count)
    except Exception as e:
        print(f"Error generating LinkedIn profiles with Gemini: {str(e)}")
        return fallback_linkedin_profiles(job_title, industry, count) 