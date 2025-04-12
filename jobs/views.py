from django.shortcuts import render, redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import JobMarket
from .services import JobFetcher, MentorFinder
from .serializers import JobMarketSerializer
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import PyPDF2
import docx
import io
import google.generativeai as genai
from django.conf import settings
from django.contrib import messages

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

def index(request):
    return render(request, 'index.html')

def skills_analysis(request):
    return render(request, 'skills_analysis.html')

def get_course_recommendations(missing_skills, target_job_title=None):
    """
    Uses the Gemini API to get course recommendations for missing skills.
    """
    model = genai.GenerativeModel('gemini-1.5-pro')  # Using the latest model

    prompt_template = """
**Role:** You are an AI Career Advisor Assistant specializing in identifying relevant online learning resources.

**Context:** A user has compared their resume skills against the requirements for a specific target job role or career path within our Intelligent Virtual Career Advisor platform. We have identified a list of skills the user is currently lacking ('missing skills') to meet the requirements of their target.

**Task:** Your primary goal is to recommend specific, high-quality online courses from reputable platforms (like Coursera, Udemy, edX, LinkedIn Learning, Udacity, Pluralsight, Khan Academy, Google Skillshop, etc.) that can help the user acquire *each* of the provided 'missing skills'.

**Input Data You Will Receive:**

1.  `missing_skills`: {missing_skills_json}
2.  `target_job_title` (Optional but helpful): "{target_job_title_str}"

**Output Requirements:**

*   Provide your response as a single, valid JSON object.
*   The main key of this object should be `course_recommendations`.
*   The value of `course_recommendations` should be a JSON object where:
    *   Each **key** is one of the *exact* skill strings provided in the `missing_skills` input list.
    *   The **value** for each skill key is a JSON list containing EXACTLY 3 recommended course objects for that specific skill, ordered by quality (best first).
    *   Each course object *must* have the following keys:
        *   `course_title`: The official title of the course (string).
        *   `platform`: The name of the platform hosting the course (string, e.g., "Coursera", "Udemy").
        *   `url`: The direct URL link to the course page (string).
        *   `level`: The estimated difficulty level (string, e.g., "Beginner", "Intermediate", "Advanced", "All Levels").
        *   `description`: A brief, one-sentence description of the course relevance.
*   Prioritize courses that are well-regarded, relevant to the `target_job_title` (if provided), and directly address the specific `missing_skill`.
*   For each skill, also include a field called `job_match_after_completion` that explains which job roles the user could qualify for after learning this skill.

**Example Interaction:**

Now, process this input:

missing_skills: {missing_skills_json}
target_job_title: "{target_job_title_str}"
"""

    # Format the input data for the prompt
    missing_skills_json_str = json.dumps(missing_skills)
    target_job_str = target_job_title if target_job_title else ""

    # Populate the prompt template
    filled_prompt = prompt_template.format(
        missing_skills_json=missing_skills_json_str,
        target_job_title_str=target_job_str
    )

    try:
        # Send the request to Gemini
        response = model.generate_content(filled_prompt)
        
        # Extract the JSON part (Gemini might add backticks or 'json')
        raw_text = response.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].strip()
        
        # Parse the JSON response
        recommendations = json.loads(raw_text)
        return recommendations

    except Exception as e:
        print(f"Error calling Gemini API for course recommendations: {e}")
        # Return an empty structure on error
        return {"course_recommendations": {skill: [] for skill in missing_skills}}

def resume_upload(request):
    if request.method == 'GET':
        return render(request, 'resume_upload.html')
    
    if request.method == 'POST':
        try:
            if 'resume' not in request.FILES:
                return JsonResponse({'error': 'No file was uploaded'}, status=400)
                
            resume_file = request.FILES['resume']
            
            # Check file extension
            file_extension = resume_file.name.split('.')[-1].lower()
            if file_extension not in ['pdf', 'docx']:
                return JsonResponse({'error': 'Only PDF and DOCX files are supported'}, status=400)
            
            # Extract text based on file type
            text = ''
            if file_extension == 'pdf':
                reader = PyPDF2.PdfReader(resume_file)
                for page in reader.pages:
                    text += page.extract_text()
            elif file_extension == 'docx':
                doc = docx.Document(resume_file)
                for para in doc.paragraphs:
                    text += para.text + '\n'
            
            # Define a set of common technical skills to look for
            technical_skills = {
                'python', 'java', 'javascript', 'typescript', 'c++', 'go', 'ruby', 'php',
                'html', 'css', 'sql', 'nosql', 'mongodb', 'mysql', 'postgresql', 'oracle',
                'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'spring',
                'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'terraform',
                'git', 'ci/cd', 'jenkins', 'github actions', 'gitlab ci',
                'machine learning', 'deep learning', 'data science', 'artificial intelligence',
                'nlp', 'computer vision', 'tensorflow', 'pytorch', 'keras',
                'algorithms', 'blockchain', 'cybersecurity', 'networking',
                'system design', 'agile', 'scrum', 'kanban'
            }
            
            # Extract technical skills from resume text
            text = text.lower()
            found_skills = []
            
            # Look for technical skills in the text
            for skill in technical_skills:
                if skill in text:
                    found_skills.append(skill)
            
            # Remove duplicates and sort
            found_skills = sorted(list(set(found_skills)))
            
            # Use existing job analysis logic
            job_markets = JobMarket.objects.all()
            results = []
            
            for job_market in job_markets:
                required_skills = job_market.required_skills
                matching_skills = [skill for skill in found_skills if skill in required_skills]
                missing_skills = [skill for skill in required_skills if skill not in found_skills]
                
                num_matching = len(matching_skills)
                num_required = len(required_skills)
                match_percentage = int((num_matching / num_required) * 100) if num_required > 0 else 0
                
                results.append({
                    'title': job_market.title,
                    'percentage': match_percentage,
                    'matching': matching_skills,
                    'missing': missing_skills
                })
            
            # Sort results by match percentage
            results.sort(key=lambda x: x['percentage'], reverse=True)
            
            # Filter out results with 0% match
            results = [result for result in results if result['percentage'] > 0]
            
            # Get the best match result
            best_match = results[0] if results else None
            
            # Get course recommendations for missing skills if there's a match
            course_recommendations = {}
            if best_match and best_match['missing']:
                # Get recommendations from Gemini API
                recommendations = get_course_recommendations(
                    best_match['missing'],
                    best_match['title']
                )
                course_recommendations = recommendations.get('course_recommendations', {})
            
            # Fetch live jobs using extracted skills for better matching
            # Use most relevant skills for job search
            search_keyword = best_match['title'] if best_match else "software"
            live_jobs = JobFetcher.fetch_all_jobs(search_keyword, found_skills)
            
            return JsonResponse({
                'extracted_skills': found_skills,
                'analysis': results,
                'live_jobs': live_jobs,
                'course_recommendations': course_recommendations
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def job_analysis(request):
    if request.method == 'POST':
        try:
            skills = request.POST.get('skills', '').split('\n')
            skills = [skill.strip().lower() for skill in skills if skill.strip()]
            
            if not skills:
                return JsonResponse({'error': 'No skills provided'}, status=400)
            
            # Get job market data
            job_markets = JobMarket.objects.all()
            results = []
            
            for job_market in job_markets:
                required_skills = job_market.required_skills
                matching_skills = [skill for skill in skills if skill in required_skills]
                missing_skills = [skill for skill in required_skills if skill not in skills]
                
                num_matching = len(matching_skills)
                num_required = len(required_skills)
                match_percentage = int((num_matching / num_required) * 100) if num_required > 0 else 0
                
                results.append({
                    'title': job_market.title,
                    'percentage': match_percentage,
                    'matching': matching_skills,
                    'missing': missing_skills
                })
            
            # Sort results by match percentage
            results.sort(key=lambda x: x['percentage'], reverse=True)
            
            # Filter out results with 0% match
            results = [result for result in results if result['percentage'] > 0]
            
            # Get the best match result
            best_match = results[0] if results else None
            
            # Get course recommendations for missing skills if there's a match
            course_recommendations = {}
            if best_match and best_match['missing']:
                # Get recommendations from Gemini API
                recommendations = get_course_recommendations(
                    best_match['missing'],
                    best_match['title']
                )
                course_recommendations = recommendations.get('course_recommendations', {})
                
                # Add information about which jobs would match if they completed all courses
                potential_matches = []
                for result in results:
                    if all(skill in best_match['missing'] for skill in result['missing']):
                        potential_matches.append(result['title'])
                        
                if potential_matches:
                    course_recommendations['potential_job_matches'] = potential_matches
            
            # Fetch live jobs using input skills for better matching
            # Use the job title that matched best with the user's skills
            search_keyword = best_match['title'] if best_match else skills[0]
            live_jobs = JobFetcher.fetch_all_jobs(search_keyword, skills)
            
            return JsonResponse({
                'analysis': results,
                'live_jobs': live_jobs,
                'course_recommendations': course_recommendations
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def networking_analysis(request):
    if request.method == 'POST':
        try:
            # Get user profile data from the request
            profile_data = {
                'current_role': request.POST.get('current_role', ''),
                'industry': request.POST.get('industry', ''),
                'skills': request.POST.get('skills', '').split(','),
                'experience': request.POST.get('experience', ''),
                'location': request.POST.get('location', ''),
                'networking_goal': request.POST.get('networking_goal', '')
            }
            
            print(f"Skills received: {profile_data['skills']}")
            
            # Get skills list
            skills = [skill.strip() for skill in profile_data['skills'] if skill.strip()]
            print(f"Processed skills: {skills}")
            
            # Always provide default mentors first
            default_mentors = [
                {
                    "name": "Career Development Mentor",
                    "profile": "https://adplist.org/mentors/career-development",
                    "skill": "Career Growth",
                    "title": "Professional Career Coach",
                    "experience": "12+ years"
                },
                {
                    "name": "Technical Skills Coach",
                    "profile": "https://adplist.org/mentors/tech-skills",
                    "skill": "Technology",
                    "title": "Senior Developer and Mentor",
                    "experience": "15 years"
                }
            ]
            
            # Directly define mentors based on skills
            mentors = list(default_mentors)  # Start with default mentors
            
            # Add guaranteed mentors for each skill
            for skill in skills:
                clean_skill = skill.strip().lower()
                print(f"Processing skill: '{clean_skill}'")
                
                # Add at least 2 mentors per skill
                if "python" in clean_skill:
                    mentors.append({
                        "name": "David Miller - Python Expert",
                        "profile": "https://adplist.org/mentors/david-miller",
                        "skill": "python",
                        "title": "Senior Python Developer at Google",
                        "experience": "10+ years"
                    })
                    mentors.append({
                        "name": "Sarah Johnson - Python Instructor",
                        "profile": "https://adplist.org/mentors/sarah-johnson",
                        "skill": "python",
                        "title": "Lead Python Instructor at Udemy",
                        "experience": "8 years"
                    })
                
                elif "javascript" in clean_skill or "js" in clean_skill:
                    mentors.append({
                        "name": "Michael Park - JavaScript Expert",
                        "profile": "https://adplist.org/mentors/michael-park",
                        "skill": "javascript",
                        "title": "Senior Frontend Developer at Meta",
                        "experience": "12 years"
                    })
                    mentors.append({
                        "name": "Jennifer Lee - JavaScript Specialist",
                        "profile": "https://adplist.org/mentors/jennifer-lee",
                        "skill": "javascript",
                        "title": "CTO at WebTech Solutions",
                        "experience": "15 years"
                    })
                
                elif "react" in clean_skill:
                    mentors.append({
                        "name": "Alex Chen - React Specialist",
                        "profile": "https://adplist.org/mentors/alex-chen",
                        "skill": "react",
                        "title": "Senior React Developer at Netflix",
                        "experience": "7 years"
                    })
                
                elif "data" in clean_skill or "science" in clean_skill:
                    mentors.append({
                        "name": "James Wilson - Data Science Expert",
                        "profile": "https://adplist.org/mentors/james-wilson",
                        "skill": "data science",
                        "title": "Lead Data Scientist at Amazon",
                        "experience": "11 years"
                    })
                
                else:
                    # Add generic mentor for any other skill
                    mentors.append({
                        "name": f"John Smith - {skill.capitalize()} Expert",
                        "profile": "https://adplist.org/mentors/john-smith",
                        "skill": skill,
                        "title": f"Senior {skill.capitalize()} Specialist",
                        "experience": "10+ years"
                    })
            
            print(f"Total mentors found: {len(mentors)}")
            
            # Construct the prompt for Gemini
            prompt = f"""
            **Role:** You are an expert Career Networking Assistant powered by Google Gemini.

            **Task:** Analyze the provided user profile summary and their networking goal. Based on this information, leverage your comprehensive knowledge of industries, companies, job roles, and career trends to suggest relevant areas for the user to focus their networking efforts.

            **Input Data:**

            1. **User Profile Summary:**
               * Current Role/Field: {profile_data['current_role']}
               * Industry: {profile_data['industry']}
               * Key Skills: {', '.join(profile_data['skills'])}
               * Years of Experience: {profile_data['experience']}
               * Location: {profile_data['location']}

            2. **User Networking Goal:**
               {profile_data['networking_goal']}

            Please provide your analysis in the following JSON format:
            {{
              "relevant_industries": [
                {{
                  "name": "Industry Name",
                  "reason": "Brief explanation of relevance"
                }}
              ],
              "example_companies": [
                {{
                  "name": "Company Name",
                  "reason": "Brief explanation of relevance"
                }}
              ],
              "relevant_role_types": [
                {{
                  "title": "Role Type",
                  "reason": "Brief explanation of relevance"
                }}
              ]
            }}
            """

            # Generate response using Gemini
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(prompt)
            
            # Parse the response
            try:
                analysis = json.loads(response.text)
                return JsonResponse({
                    'status': 'success',
                    'analysis': analysis,
                    'mentors': mentors,
                    'debug': {
                        'skills_received': skills,
                        'mentor_count': len(mentors)
                    }
                })
            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to parse analysis results',
                    'mentors': mentors,
                    'debug': {
                        'skills_received': skills,
                        'mentor_count': len(mentors)
                    }
                }, status=500)

        except Exception as e:
            print(f"Networking analysis error: {e}")
            # Even in case of error, return some mentor data
            fallback_mentors = [
                {
                    "name": "Professional Mentor - Fallback",
                    "profile": "https://adplist.org/mentors/professional-mentor",
                    "skill": "Career Development",
                    "title": "Career Coach and Mentor",
                    "experience": "15+ years"
                }
            ]
            return JsonResponse({
                'status': 'error',
                'message': str(e),
                'mentors': fallback_mentors,
                'debug': {
                    'error': str(e)
                }
            }, status=500)

    return render(request, 'networking_analysis.html')

def job_listings(request):
    """View for displaying all job listings with search functionality"""
    # Get query parameters for filtering
    search_query = request.GET.get('query', '')
    
    # Start with all jobs or search for jobs
    if search_query:
        # Use JobFetcher to get jobs based on the search query
        # Try to extract skills from the search query for better matching
        skills = [skill.strip() for skill in search_query.split(',') if skill.strip()]
        jobs = JobFetcher.fetch_all_jobs(search_query, skills)
    else:
        # If no search query, just fetch some default jobs
        jobs = JobFetcher.fetch_all_jobs("software developer")
    
    context = {
        'jobs': jobs,
        'search_query': search_query
    }
    
    return render(request, 'jobs/job_listings.html', context)

def job_detail(request, job_id):
    """View for displaying details of a specific job"""
    # In a real implementation, we would fetch the job from the database
    # For now, we'll redirect to job listings since we're using external API data
    messages.info(request, "Job details are provided via external sources. Please use the direct link.")
    return redirect('jobs:job_listings')

def search_jobs(request):
    """API view for searching jobs based on keywords"""
    if request.method == 'GET':
        keyword = request.GET.get('keyword', '')
        skills = request.GET.get('skills', '')
        
        if not keyword:
            return JsonResponse({'error': 'Keyword is required'}, status=400)
        
        # Parse skills if provided
        skills_list = None
        if skills:
            skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        
        jobs = JobFetcher.fetch_all_jobs(keyword, skills_list)
        return JsonResponse({'jobs': jobs})
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def recommended_jobs(request):
    """View for displaying personalized job recommendations"""
    # This view will primarily use JavaScript to fetch recommended jobs
    # based on the user's profile skills
    return render(request, 'jobs/recommended_jobs.html') 