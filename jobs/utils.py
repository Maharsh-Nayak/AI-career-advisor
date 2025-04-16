import re
import random
import requests
import json
from urllib.parse import quote
from django.conf import settings

# Try to import spaCy and define global availability flag
SPACY_AVAILABLE = False
nlp = None

try:
    import spacy
    SPACY_AVAILABLE = True
    try:
        nlp = spacy.load("en_core_web_sm")
        print("INFO: Successfully loaded spaCy model.")
    except Exception as e:
        print(f"WARNING: Could not load spaCy model: {str(e)}. Some features may be limited.")
except ImportError:
    print("WARNING: spaCy is not available. Using fallback functions.")

# Import fallback functions
try:
    from .utils_fallback import (
        fallback_extract_keywords,
        fallback_match_suggestions,
        generate_linkedin_search_url,
        generate_linkedin_profiles_with_gemini,
        fallback_linkedin_profiles
    )
except ImportError:
    print("WARNING: utils_fallback.py not found. Some features may not work.")
    # Simple fallback definitions if the import fails
    def fallback_extract_keywords(text):
        """Simple fallback method for keyword extraction"""
        words = text.lower().split()
        return [w for w in words if len(w) > 3]
        
    def fallback_match_suggestions(user_skills, job_skills):
        """Simple fallback for skill matching"""
        return list(set(user_skills).intersection(set(job_skills)))

def extract_keywords(goal_text):
    """Extract keywords from networking goal text using NLP"""
    
    if not SPACY_AVAILABLE or nlp is None:
        # Fallback method if spaCy not available or model not loaded
        return fallback_extract_keywords(goal_text)
    
    # Process the text with spaCy
    doc = nlp(goal_text.lower())
    
    # Extract noun chunks (meaningful phrases)
    keywords = [chunk.text for chunk in doc.noun_chunks if len(chunk.text.split()) <= 3]
    
    # Add specific roles and job titles with improved detection
    job_title_indicators = [
        # Technical roles
        "engineer", "developer", "architect", "programmer", "administrator", "technician", 
        "devops", "sre", "designer", "specialist", "analyst", "scientist", "researcher",
        # Management roles
        "manager", "director", "lead", "head", "chief", "consultant", 
        # Technology specializations
        "frontend", "backend", "fullstack", "mobile", "ios", "android", "web", "cloud", 
        "security", "network", "systems", "database", "data", "ml", "ai", "ui", "ux",
        # Programming languages
        "python", "java", "javascript", "typescript", "react", "angular", "vue", "node",
        "php", "ruby", "go", "rust", "c#", "c++", "swift", "kotlin", "scala",
        # Technical skills
        "api", "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "sql", "nosql",
        "blockchain", "cybersecurity", "machine learning", "deep learning", "nlp",
        "testing", "qa", "linux", "unix", "windows", "cisco", "agile", "scrum"
    ]
    
    # Common technical compound terms to look for directly
    compound_tech_terms = [
        "machine learning", "deep learning", "artificial intelligence", "natural language processing",
        "data science", "data engineering", "data analysis", "big data", "business intelligence",
        "cloud computing", "devops engineer", "site reliability", "full stack", "front end", "back end",
        "software development", "web development", "mobile development", "game development",
        "network security", "information security", "cyber security", "database administrator",
        "systems architect", "ui/ux", "user interface", "user experience"
    ]
    
    # Check for specific technical compound terms
    for term in compound_tech_terms:
        if term in goal_text.lower() and term not in keywords:
            keywords.append(term)
    
    for token in doc:
        # Add proper nouns as they might be company names or specific technologies
        if token.pos_ == "PROPN" and len(token.text) > 2 and token.text not in keywords:
            keywords.append(token.text)
        
        # Improve job title detection
        if token.text in job_title_indicators and token.i > 0:
            # Check for job titles (e.g., "data scientist", "product manager")
            potential_title = doc[token.i-1].text + " " + token.text
            if potential_title not in keywords:
                keywords.append(potential_title)
            
            # Look for 3-word titles like "senior software engineer"
            if token.i > 1:
                three_word_title = doc[token.i-2].text + " " + doc[token.i-1].text + " " + token.text
                if three_word_title not in keywords:
                    keywords.append(three_word_title)
                
        # Check for technology stack patterns like "X developer" or "X engineer"
        if token.text in ["developer", "engineer", "specialist", "professional"] and token.i > 0:
            tech_role = doc[token.i-1].text + " " + token.text
            if tech_role not in keywords:
                keywords.append(tech_role)
    
    # Extract skill and industry terms using entities with improved detection
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART", "GPE"] and ent.text not in keywords:
            keywords.append(ent.text)
    
    # Clean up and normalize keywords
    clean_keywords = []
    for keyword in keywords:
        keyword = keyword.strip()
        # Remove articles and other stop words at the beginning
        keyword = re.sub(r'^(a|an|the)\s+', '', keyword)
        if keyword and len(keyword) > 2:  # Only keep meaningful keywords
            clean_keywords.append(keyword)
    
    return list(set(clean_keywords))  # Remove duplicates

def match_suggestions(user_skills, job_skills):
    """Match user skills with job skills"""
    if not SPACY_AVAILABLE or nlp is None:
        # Use fallback when spaCy is not available or model not loaded
        return fallback_match_suggestions(user_skills, job_skills)
    
    try:
        # Process with spaCy for better matching
        common_skills = set(user_skills).intersection(set(job_skills))
        
        # Also look for similar skills (that might be phrased differently)
        similar_skills = []
        for user_skill in user_skills:
            user_doc = nlp(user_skill.lower())
            for job_skill in job_skills:
                if job_skill.lower() in common_skills:
                    continue  # Skip already matched skills
                
                job_doc = nlp(job_skill.lower())
                similarity = user_doc.similarity(job_doc)
                
                # High similarity threshold to avoid false positives
                if similarity > 0.8:
                    similar_skills.append((user_skill, job_skill, similarity))
        
        # Add the highest similarity matches that aren't already exact matches
        similar_skills.sort(key=lambda x: x[2], reverse=True)
        
        # Add top similar skills (up to 5)
        top_similar = [pair[0] for pair in similar_skills[:5]]
        
        return list(common_skills) + top_similar
    except Exception as e:
        print(f"Error using spaCy for skill matching: {str(e)}")
        return fallback_match_suggestions(user_skills, job_skills)

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

def fallback_linkedin_profiles(job_title, industry=None, count=3):
    """Generate mock LinkedIn profiles when Gemini API is unavailable"""
    companies = [
        "Google", "Microsoft", "Amazon", "Apple", "Meta", "IBM", "Oracle", 
        "Intel", "Cisco", "Adobe", "Salesforce", "Twitter", "LinkedIn", 
        "Netflix", "Spotify", "Airbnb", "Uber", "Tesla"
    ]
    
    locations = [
        "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX", 
        "Boston, MA", "Chicago, IL", "Los Angeles, CA", "Denver, CO", 
        "Atlanta, GA", "Toronto, Canada", "London, UK", "Berlin, Germany"
    ]
    
    schools = [
        "Stanford University", "MIT", "Harvard University", "UC Berkeley",
        "Carnegie Mellon University", "Georgia Tech", "University of Washington",
        "University of Michigan", "Cornell University", "Columbia University"
    ]
    
    degrees = ["BS", "BA", "MS", "MBA", "PhD"]
    
    fields = ["Computer Science", "Information Technology", "Business Administration", 
              "Data Science", "Engineering", "Mathematics", "Economics"]
    
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", 
                  "Linda", "William", "Elizabeth", "David", "Susan", "Richard", "Jessica", 
                  "Joseph", "Sarah", "Thomas", "Karen", "Charles", "Nancy"]
    
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", 
                 "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", 
                 "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
    
    job_skills = {
        "Software Engineer": ["Python", "JavaScript", "Java", "React", "Node.js", "AWS", "Git", "SQL", "Docker"],
        "Data Scientist": ["Python", "R", "SQL", "Machine Learning", "TensorFlow", "PyTorch", "Data Visualization", "Statistics"],
        "Product Manager": ["Product Strategy", "Agile", "User Research", "Roadmapping", "Market Analysis", "A/B Testing"],
        "UX Designer": ["Figma", "User Research", "Wireframing", "Prototyping", "Usability Testing", "UI Design"],
        "Marketing Manager": ["Digital Marketing", "SEO", "Content Strategy", "Social Media", "Brand Management", "Analytics"],
        "Financial Analyst": ["Financial Modeling", "Excel", "Forecasting", "Budgeting", "Accounting", "Data Analysis"],
        "HR Manager": ["Recruitment", "Employee Relations", "Performance Management", "Compensation", "HR Policies"],
        "Project Manager": ["Agile", "Scrum", "Project Planning", "Risk Management", "Stakeholder Management", "JIRA"]
    }
    
    # Get skills for the specified job title, or use generic skills
    if job_title in job_skills:
        skills_pool = job_skills[job_title]
    else:
        # Generic skills that could apply to many roles
        skills_pool = ["Communication", "Leadership", "Problem Solving", "Teamwork", 
                      "Project Management", "Strategic Thinking", "Time Management", 
                      "Critical Thinking", "Creativity", "Decision Making"]
    
    profiles = []
    for i in range(count):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        company = random.choice(companies)
        
        # Select 3-5 random skills for this profile
        num_skills = random.randint(3, 5)
        profile_skills = random.sample(skills_pool, min(num_skills, len(skills_pool)))
        
        school = random.choice(schools)
        degree = random.choice(degrees)
        field = random.choice(fields)
        grad_year = random.randint(2010, 2023)
        
        location = random.choice(locations)
        
        # Create a realistic-looking profile
        profile = {
            "name": f"{first_name} {last_name}",
            "title": job_title,
            "company": company,
            "location": location,
            "summary": f"Experienced {job_title} with a passion for {profile_skills[0]} and {profile_skills[1]}. " +
                      f"{random.randint(3, 15)} years of experience in the {industry if industry else 'technology'} industry.",
            "skills": profile_skills,
            "education": f"{degree} in {field}, {school}, {grad_year}",
            "linkedin_url": f"https://www.linkedin.com/in/{first_name.lower()}-{last_name.lower()}-{random.randint(100, 999)}"
        }
        
        profiles.append(profile)
    
    return profiles 