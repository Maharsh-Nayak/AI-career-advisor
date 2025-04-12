import spacy
import re

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    # Fallback if model not available
    nlp = None

def extract_keywords(goal_text):
    """Extract keywords from networking goal text using NLP"""
    
    if nlp is None:
        # Fallback method if spaCy not available
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

def fallback_extract_keywords(goal_text):
    """Fallback method for keyword extraction without NLP"""
    # Convert to lowercase for consistency
    text = goal_text.lower()
    
    # Define common networking-related terms to look for
    roles = ["mentor", "data scientist", "engineer", "developer", "designer", 
             "manager", "director", "analyst", "consultant", "specialist"]
    
    industries = ["tech", "technology", "gaming", "finance", "healthcare", 
                 "renewable energy", "education", "retail", "media", "manufacturing"]
    
    objectives = ["learn", "connect", "explore", "find", "network", "discover", 
                 "grow", "advance", "improve", "develop"]
    
    # Extract words from the text
    words = re.findall(r'\b\w+\b', text)
    
    # Initialize keyword categories
    extracted_keywords = []
    
    # Find roles
    for role in roles:
        if role in text:
            extracted_keywords.append(role)
    
    # Find industries
    for industry in industries:
        if industry in text:
            extracted_keywords.append(industry)
    
    # Find objectives
    for objective in objectives:
        if objective in text:
            extracted_keywords.append(objective)
    
    # Look for 2-word phrases (e.g., "data science")
    phrases = []
    for i in range(len(words) - 1):
        phrase = f"{words[i]} {words[i+1]}"
        if any(role in phrase for role in roles) or any(industry in phrase for industry in industries):
            phrases.append(phrase)
    
    return list(set(extracted_keywords + phrases))

def match_suggestions(keywords):
    """Map extracted keywords to industry, company, and role suggestions"""
    industries = []
    companies = []
    roles = []
    
    # Add improved specificity to industry mapping
    industry_keywords = {
        'tech': 'Technology',
        'technology': 'Technology',
        'software': 'Technology',
        'gaming': 'Gaming & Entertainment',
        'game': 'Gaming & Entertainment',
        'health': 'Healthcare & Biotechnology',
        'healthcare': 'Healthcare & Biotechnology',
        'medical': 'Healthcare & Biotechnology',
        'finance': 'Finance & Banking',
        'banking': 'Finance & Banking',
        'financial': 'Finance & Banking',
        'education': 'Education & E-learning',
        'learning': 'Education & E-learning',
        'teach': 'Education & E-learning',
        'renewable': 'Renewable Energy',
        'energy': 'Energy & Utilities',
        'retail': 'Retail & E-commerce',
        'ecommerce': 'Retail & E-commerce',
        'advertising': 'Marketing & Advertising',
        'marketing': 'Marketing & Advertising',
        'media': 'Media & Communications',
        'ai': 'Artificial Intelligence',
        'artificial intelligence': 'Artificial Intelligence',
        'machine learning': 'Artificial Intelligence',
        'data': 'Data Science & Analytics',
        'crypto': 'Blockchain & Cryptocurrency',
        'blockchain': 'Blockchain & Cryptocurrency',
        'legal': 'Legal & Compliance',
        'law': 'Legal & Compliance',
        'food': 'Food & Beverage',
        'restaurant': 'Food & Beverage',
        'hospitality': 'Travel & Hospitality',
        'travel': 'Travel & Hospitality',
        'automotive': 'Automotive & Transportation',
        'transport': 'Automotive & Transportation',
        'manufacturing': 'Manufacturing & Industrial',
        'industrial': 'Manufacturing & Industrial'
    }
    
    # Role mapping
    role_keywords = {
        # Development roles
        'developer': 'Software Developer',
        'engineer': 'Engineer',
        'software engineer': 'Software Engineer',
        'programmer': 'Programmer',
        'coder': 'Programmer',
        'architect': 'Solutions Architect',
        'devops': 'DevOps Engineer',
        'sre': 'Site Reliability Engineer',
        'fullstack': 'Full Stack Developer',
        'full stack': 'Full Stack Developer',
        'frontend': 'Frontend Developer',
        'front end': 'Frontend Developer',
        'backend': 'Backend Developer',
        'back end': 'Backend Developer',
        'mobile': 'Mobile Developer',
        'ios': 'iOS Developer',
        'android': 'Android Developer',
        'web': 'Web Developer',
        
        # Design roles
        'designer': 'Designer',
        'ui': 'UI Designer',
        'ux': 'UX Designer',
        'ui/ux': 'UI/UX Designer',
        'user interface': 'UI Designer',
        'user experience': 'UX Designer',
        'graphic': 'Graphic Designer',
        
        # Data roles
        'data': 'Data Professional',
        'data scientist': 'Data Scientist',
        'data science': 'Data Scientist',
        'data engineer': 'Data Engineer',
        'analyst': 'Data Analyst',
        'business intelligence': 'BI Analyst',
        'database': 'Database Administrator',
        'dba': 'Database Administrator',
        
        # Security roles
        'security': 'Security Engineer',
        'cybersecurity': 'Cybersecurity Specialist',
        'cyber security': 'Cybersecurity Specialist',
        'network security': 'Network Security Engineer',
        'information security': 'Information Security Analyst',
        
        # Management roles
        'scientist': 'Scientist',
        'researcher': 'Researcher',
        'lead': 'Team Lead',
        'manager': 'Manager',
        'director': 'Director',
        'head': 'Department Head',
        'chief': 'Chief Officer',
        'cto': 'Chief Technology Officer',
        'cio': 'Chief Information Officer',
        'ceo': 'Chief Executive Officer',
        
        # Other professional roles
        'marketer': 'Marketing Specialist',
        'consultant': 'Consultant',
        'mentor': 'Mentor',
        'coach': 'Career Coach',
        'advisor': 'Advisor',
        'recruiter': 'Recruiter',
        'hr': 'HR Professional',
        'project manager': 'Project Manager',
        'product manager': 'Product Manager',
        'scrum master': 'Scrum Master',
        'qa': 'QA Engineer',
        'quality assurance': 'QA Engineer',
        'tester': 'QA Engineer',
        'technical writer': 'Technical Writer',
        'cloud engineer': 'Cloud Engineer',
        'systems administrator': 'Systems Administrator',
        'network administrator': 'Network Administrator'
    }
    
    # Company mapping based on industry
    company_by_industry = {
        'Technology': ['Google', 'Microsoft', 'Apple', 'Amazon', 'Meta'],
        'Gaming & Entertainment': ['Electronic Arts', 'Ubisoft', 'Epic Games', 'Activision Blizzard', 'Nintendo'],
        'Healthcare & Biotechnology': ['Johnson & Johnson', 'Pfizer', 'Roche', 'Novartis', 'Medtronic'],
        'Finance & Banking': ['JPMorgan Chase', 'Goldman Sachs', 'Morgan Stanley', 'Bank of America', 'Citigroup'],
        'Education & E-learning': ['Coursera', 'Udemy', 'edX', 'Khan Academy', 'Chegg'],
        'Renewable Energy': ['Tesla', 'NextEra Energy', 'First Solar', 'Siemens Gamesa', 'Vestas'],
        'Retail & E-commerce': ['Walmart', 'Amazon', 'Shopify', 'Target', 'Alibaba'],
        'Marketing & Advertising': ['WPP', 'Omnicom', 'Publicis', 'Interpublic', 'HubSpot'],
        'Media & Communications': ['Disney', 'Warner Bros', 'Netflix', 'Comcast', 'Sony'],
        'Artificial Intelligence': ['OpenAI', 'DeepMind', 'NVIDIA', 'IBM', 'SenseTime'],
        'Data Science & Analytics': ['Databricks', 'Palantir', 'Snowflake', 'Tableau', 'SAS']
    }
    
    # Map keywords to industries
    for keyword in keywords:
        for key, industry in industry_keywords.items():
            if key in keyword.lower():
                if industry not in industries:
                    industries.append(industry)
    
    # Map keywords to roles
    for keyword in keywords:
        for key, role in role_keywords.items():
            if key in keyword.lower():
                if role not in roles:
                    roles.append(role)
    
    # Generate company suggestions based on identified industries
    for industry in industries:
        if industry in company_by_industry:
            # Add 3 companies from each matched industry
            companies.extend(company_by_industry[industry][:3])
    
    # Default suggestions if nothing was matched
    if not industries:
        industries = ['Technology', 'Business Services']
    if not roles:
        roles = ['Business Professional', 'Networking Specialist']
    if not companies:
        companies = ['LinkedIn', 'Indeed', 'Glassdoor']
    
    # Format the output with reasons
    formatted_industries = [{"name": industry, "reason": f"Based on your networking goals"} for industry in industries[:5]]
    formatted_roles = [{"title": role, "reason": f"Relevant to your career interests"} for role in roles[:5]]
    formatted_companies = [{"name": company, "reason": f"Leading organization in {industries[0] if industries else 'your field'}"} for company in companies[:5]]
    
    return {
        "relevant_industries": formatted_industries,
        "example_companies": formatted_companies,
        "relevant_role_types": formatted_roles
    }

def generate_linkedin_search_url(role, industry):
    """Generate a LinkedIn search URL for finding mentors"""
    # Clean and encode the role and industry for search
    role_query = role.replace(" ", "%20")
    industry_query = industry.replace(" ", "%20")
    
    # Create a more targeted LinkedIn search that specifically looks for mentors in the role/industry
    return f"https://www.linkedin.com/search/results/people/?keywords={role_query}%20{industry_query}%20mentor&origin=GLOBAL_SEARCH_HEADER&sid=)LB"

def generate_linkedin_profiles_with_gemini(networking_goal, extracted_keywords):
    """Use Gemini API to generate optimized LinkedIn search queries and profile recommendations"""
    from google.generativeai import GenerativeModel
    from django.conf import settings
    import json
    
    try:
        model = GenerativeModel('gemini-1.5-pro')
        
        prompt = f"""
        As a career networking expert, analyze the user's networking goal and extracted keywords below to create optimized LinkedIn profile search recommendations.
        
        User's Networking Goal: "{networking_goal}"
        
        Extracted Keywords: {json.dumps(extracted_keywords)}
        
        Based on this information, create EXACTLY 4 highly-specific LinkedIn profile searches that would help the user connect with the most relevant professionals. For each search:
        
        1. Create a precise LinkedIn search query string (what would go in the search box)
        2. Specify the exact role/position title to search for
        3. Specify the industry/sector to focus on
        4. Add any additional search parameters that would improve results (like years of experience, specific skills, etc.)
        5. Briefly explain why this particular search would be valuable for the user
        
        Format your response as a JSON array of objects with these fields:
        - search_query: The full search string to use (3-6 keywords max)
        - role: The specific role/title
        - industry: The specific industry
        - additional_params: Any other search parameters
        - description: Brief explanation of why this search is relevant
        - url: The complete LinkedIn search URL for this query
        
        Make your searches highly targeted and specific to the user's goal. Focus on finding potential mentors, industry experts, and professionals who could provide meaningful connections.
        """
        
        # Get the response from Gemini
        response = model.generate_content(prompt)
        
        # Extract the JSON from the response
        raw_text = response.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].strip()
        
        # Parse the JSON response
        linkedin_profiles = json.loads(raw_text)
        
        # Format the URLs correctly
        for profile in linkedin_profiles:
            # Ensure search query is properly URL encoded
            search_query = profile["search_query"].replace(" ", "%20")
            
            # Create the proper LinkedIn search URL with the optimized query
            profile["url"] = f"https://www.linkedin.com/search/results/people/?keywords={search_query}&origin=GLOBAL_SEARCH_HEADER"
            
            # Add primary flag for the first two results
            profile["primary"] = linkedin_profiles.index(profile) < 2
        
        return linkedin_profiles
        
    except Exception as e:
        print(f"Error using Gemini API for LinkedIn profiles: {e}")
        # Return a simple fallback structure
        return [
            {
                "search_query": "experienced mentor",
                "role": "Career Mentor",
                "industry": "Career Development",
                "additional_params": "5+ years experience",
                "description": "General career mentors can help with networking strategy",
                "url": "https://www.linkedin.com/search/results/people/?keywords=experienced%20mentor&origin=GLOBAL_SEARCH_HEADER",
                "primary": True
            }
        ] 