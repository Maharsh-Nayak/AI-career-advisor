from django.shortcuts import render, redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import JobMarket, CourseRecommendation, SavedJob
from .services import JobFetcher, MentorFinder, CourseRecommender
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
import re
from django.contrib.auth.decorators import login_required

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

def index(request):
    return render(request, 'index.html')

def skills_analysis(request):
    # Test the API key first
    is_valid, message = test_gemini_api()
    if not is_valid:
        messages.error(request, f"Gemini API Error: {message}")
    return render(request, 'skills_analysis.html')

def get_course_recommendations(missing_skills, target_job_title=None):
    """
    Uses the Gemini API to get course recommendations for missing skills.
    """
    model = genai.GenerativeModel('gemini-1.5-pro')  # Using the latest model

    # First verify API key is configured
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == 'AIzaSyCphmUSSXd-TpUbu2q2pBJTV9bsV1wmM4Q':
        error_msg = "Gemini API key is not properly configured. Please set up a valid API key in your .env file."
        print(error_msg)
        return {"error": error_msg}

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
        
        if not response or not response.text:
            error_msg = "Received empty response from Gemini API"
            print(error_msg)
            return {"error": error_msg}
            
        # Extract the JSON part (Gemini might add backticks or 'json')
        raw_text = response.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].strip()
        
        try:
            # Parse the JSON response
            recommendations = json.loads(raw_text)
            return recommendations
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse Gemini API response as JSON: {str(e)}"
            print(error_msg)
            print("Raw response:", raw_text)
            return {"error": error_msg}

    except Exception as e:
        error_msg = f"Error calling Gemini API for course recommendations: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

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
            try:
                if file_extension == 'pdf':
                    reader = PyPDF2.PdfReader(resume_file)
                    for page in reader.pages:
                        text += page.extract_text()
                elif file_extension == 'docx':
                    doc = docx.Document(resume_file)
                    for para in doc.paragraphs:
                        text += para.text + '\n'
                
                if not text.strip():
                    return JsonResponse({'error': 'Could not extract text from the uploaded file'}, status=400)
                    
            except Exception as e:
                print(f"Error extracting text from file: {str(e)}")
                return JsonResponse({'error': 'Error reading the uploaded file. Please ensure it is not corrupted.'}, status=400)
            
            # Print the extracted text for debugging
            print("Extracted text from resume:", text[:500])  # Print first 500 chars
            
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
            skill_locations = {}  # Store where each skill was found
            
            # Improved skill detection with location tracking
            for skill in technical_skills:
                skill_pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                matches = list(re.finditer(skill_pattern, text))
                if matches:
                    found_skills.append(skill)
                    skill_locations[skill] = [(m.start(), m.end()) for m in matches]
            
            # Additional common variations of skills
            skill_variations = {
                'js': 'javascript',
                'node': 'node.js',
                'react.js': 'react',
                'vue.js': 'vue',
                'postgres': 'postgresql',
                'ml': 'machine learning',
                'ai': 'artificial intelligence',
                'cv': 'computer vision'
            }
            
            # Check for skill variations
            for variation, main_skill in skill_variations.items():
                variation_pattern = r'\b' + re.escape(variation.lower()) + r'\b'
                matches = list(re.finditer(variation_pattern, text))
                if matches and main_skill not in found_skills:
                    found_skills.append(main_skill)
                    skill_locations[f"{main_skill} (as '{variation}')"] = [(m.start(), m.end()) for m in matches]
            
            # Remove duplicates and sort
            found_skills = sorted(list(set(found_skills)))
            
            print("Final found skills:", found_skills)  # Debug print
            
            # Get job market data and ensure we have some data
            job_markets = JobMarket.objects.all()
            if not job_markets.exists():
                # Create default job markets if none exist
                default_jobs = [
                    {
                        'title': 'Full Stack Developer',
                        'required_skills': ['python', 'javascript', 'html', 'css', 'react', 'django']
                    },
                    {
                        'title': 'Data Scientist',
                        'required_skills': ['python', 'machine learning', 'data science', 'sql']
                    },
                    {
                        'title': 'DevOps Engineer',
                        'required_skills': ['docker', 'kubernetes', 'aws', 'ci/cd', 'terraform']
                    },
                    {
                        'title': 'Frontend Developer',
                        'required_skills': ['html', 'css', 'javascript', 'react', 'typescript']
                    },
                    {
                        'title': 'Backend Developer',
                        'required_skills': ['python', 'django', 'postgresql', 'api development', 'docker']
                    },
                    {
                        'title': 'Machine Learning Engineer',
                        'required_skills': ['python', 'machine learning', 'deep learning', 'tensorflow', 'pytorch']
                    }
                ]
                
                for job in default_jobs:
                    JobMarket.objects.create(
                        title=job['title'],
                        required_skills=job['required_skills']
                    )
                
                job_markets = JobMarket.objects.all()
            
            results = []
            for job_market in job_markets:
                required_skills = job_market.required_skills
                
                # Calculate matching and missing skills
                matching_skills = [skill for skill in found_skills if skill in required_skills]
                missing_skills = [skill for skill in required_skills if skill not in found_skills]
                extra_skills = [skill for skill in found_skills if skill not in required_skills]
                
                # Calculate match metrics
                num_matching = len(matching_skills)
                num_required = len(required_skills)
                num_extra = len(extra_skills)
                
                # Calculate different percentages
                match_percentage = int((num_matching / num_required) * 100) if num_required > 0 else 0
                completeness_score = int((num_matching / (num_matching + len(missing_skills))) * 100) if (num_matching + len(missing_skills)) > 0 else 0
                
                # Calculate relevance score (considers both matches and extras)
                relevance_score = (match_percentage * 0.7) + (completeness_score * 0.3)
                
                job_result = {
                    'title': job_market.title,
                    'match_percentage': match_percentage,
                    'completeness_score': completeness_score,
                    'relevance_score': round(relevance_score, 2),
                    'matching_skills': matching_skills,
                    'missing_skills': missing_skills,
                    'extra_skills': extra_skills,
                    'required_skills': required_skills,
                    'analysis': {
                        'total_required': num_required,
                        'total_matching': num_matching,
                        'total_missing': len(missing_skills),
                        'total_extra': num_extra
                    }
                }
                
                results.append(job_result)
            
            # Sort results by relevance score (primary) and match percentage (secondary)
            results.sort(key=lambda x: (x['relevance_score'], x['match_percentage']), reverse=True)
            
            # Filter out results with 0% match
            results = [result for result in results if result['match_percentage'] > 0]
            
            # Get the top match
            best_match = results[0] if results else None
            
            # Get course recommendations for missing skills
            course_recommendations = {}
            if best_match and best_match['missing_skills']:
                # Get recommendations with current skills context
                recommendations = get_course_recommendations(
                    best_match['missing_skills'],
                    best_match['title']
                )
                
                if 'error' not in recommendations:
                    course_recommendations = recommendations.get('course_recommendations', {})
                    
                    # Add potential job matches after completing courses
                    potential_matches = []
                    for result in results:
                        # Check if completing the courses would qualify for this job
                        if all(skill in best_match['missing_skills'] for skill in result['missing_skills']):
                            potential_matches.append({
                                'title': result['title'],
                                'current_match': result['match_percentage'],
                                'potential_match': 100
                            })
                    
                    if potential_matches:
                        course_recommendations['potential_job_matches'] = potential_matches
            
            # Fetch live job listings that match the user's skills
            live_jobs = []
            if best_match:
                # Use both matching skills and job title for better results
                search_terms = [best_match['title']] + best_match['matching_skills']
                for term in search_terms:
                    jobs = JobFetcher.fetch_all_jobs(term, best_match['matching_skills'])
                    live_jobs.extend(jobs)
                
                # Remove duplicates while preserving order
                seen = set()
                unique_jobs = []
                for job in live_jobs:
                    job_key = (job.get('title', ''), job.get('company', ''))
                    if job_key not in seen:
                        seen.add(job_key)
                        unique_jobs.append(job)
                
                live_jobs = unique_jobs[:10]  # Limit to top 10 most relevant jobs
            
            response_data = {
                'status': 'success',
                'analysis': {
                    'results': results,
                    'best_match': best_match,
                    'total_matches': len(results),
                    'skills_analyzed': len(found_skills)
                },
                'extracted_skills': found_skills,
                'skill_locations': skill_locations,
                'live_jobs': live_jobs,
                'course_recommendations': course_recommendations
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            print(f"Error processing resume: {str(e)}")  # Log the error
            return JsonResponse({
                'error': 'An error occurred while processing your resume. Please try again.'
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def job_analysis(request):
    if request.method == 'POST':
        try:
            # Get skills from request and clean them
            skills = request.POST.get('skills', '').split('\n')
            skills = [skill.strip().lower() for skill in skills if skill.strip()]
            
            if not skills:
                return JsonResponse({'error': 'No skills provided'}, status=400)
            
            print("Analyzing skills:", skills)  # Debug print
            
            # Get job market data and ensure we have some data
            job_markets = JobMarket.objects.all()
            if not job_markets.exists():
                # Create default job markets if none exist
                default_jobs = [
                    {
                        'title': 'Full Stack Developer',
                        'required_skills': ['python', 'javascript', 'html', 'css', 'react', 'django']
                    },
                    {
                        'title': 'Data Scientist',
                        'required_skills': ['python', 'machine learning', 'data science', 'sql']
                    },
                    {
                        'title': 'DevOps Engineer',
                        'required_skills': ['docker', 'kubernetes', 'aws', 'ci/cd', 'terraform']
                    },
                    {
                        'title': 'Frontend Developer',
                        'required_skills': ['html', 'css', 'javascript', 'react', 'typescript']
                    },
                    {
                        'title': 'Backend Developer',
                        'required_skills': ['python', 'django', 'postgresql', 'api development', 'docker']
                    },
                    {
                        'title': 'Machine Learning Engineer',
                        'required_skills': ['python', 'machine learning', 'deep learning', 'tensorflow', 'pytorch']
                    }
                ]
                
                for job in default_jobs:
                    JobMarket.objects.create(
                        title=job['title'],
                        required_skills=job['required_skills']
                    )
                
                job_markets = JobMarket.objects.all()
            
            results = []
            for job_market in job_markets:
                required_skills = job_market.required_skills
                
                # Calculate matching and missing skills
                matching_skills = [skill for skill in skills if skill in required_skills]
                missing_skills = [skill for skill in required_skills if skill not in skills]
                extra_skills = [skill for skill in skills if skill not in required_skills]
                
                # Calculate match metrics
                num_matching = len(matching_skills)
                num_required = len(required_skills)
                num_extra = len(extra_skills)
                
                # Calculate different percentages
                match_percentage = int((num_matching / num_required) * 100) if num_required > 0 else 0
                completeness_score = int((num_matching / (num_matching + len(missing_skills))) * 100) if (num_matching + len(missing_skills)) > 0 else 0
                
                # Calculate relevance score (considers both matches and extras)
                relevance_score = (match_percentage * 0.7) + (completeness_score * 0.3)
                
                job_result = {
                    'title': job_market.title,
                    'match_percentage': match_percentage,
                    'completeness_score': completeness_score,
                    'relevance_score': round(relevance_score, 2),
                    'matching_skills': matching_skills,
                    'missing_skills': missing_skills,
                    'extra_skills': extra_skills,
                    'required_skills': required_skills,
                    'analysis': {
                        'total_required': num_required,
                        'total_matching': num_matching,
                        'total_missing': len(missing_skills),
                        'total_extra': num_extra
                    }
                }
                
                results.append(job_result)
            
            # Sort results by relevance score (primary) and match percentage (secondary)
            results.sort(key=lambda x: (x['relevance_score'], x['match_percentage']), reverse=True)
            
            # Filter out results with 0% match
            results = [result for result in results if result['match_percentage'] > 0]
            
            # Get the top match
            best_match = results[0] if results else None
            
            # Get course recommendations for missing skills
            course_recommendations = {}
            if best_match and best_match['missing_skills']:
                recommendations = get_course_recommendations(
                    best_match['missing_skills'],
                    best_match['title']
                )
                
                if 'error' not in recommendations:
                    course_recommendations = recommendations.get('course_recommendations', {})
                    
                    # Add potential job matches after completing courses
                    potential_matches = []
                    for result in results:
                        # Check if completing the courses would qualify for this job
                        if all(skill in best_match['missing_skills'] for skill in result['missing_skills']):
                            potential_matches.append({
                                'title': result['title'],
                                'current_match': result['match_percentage'],
                                'potential_match': 100
                            })
                    
                    if potential_matches:
                        course_recommendations['potential_job_matches'] = potential_matches
            
            # Fetch live job listings that match the user's skills
            live_jobs = []
            if best_match:
                # Use both matching skills and job title for better results
                search_terms = [best_match['title']] + best_match['matching_skills']
                for term in search_terms:
                    jobs = JobFetcher.fetch_all_jobs(term, best_match['matching_skills'])
                    live_jobs.extend(jobs)
                
                # Remove duplicates while preserving order
                seen = set()
                unique_jobs = []
                for job in live_jobs:
                    job_key = (job.get('title', ''), job.get('company', ''))
                    if job_key not in seen:
                        seen.add(job_key)
                        unique_jobs.append(job)
                
                live_jobs = unique_jobs[:10]  # Limit to top 10 most relevant jobs
            
            response_data = {
                'status': 'success',
                'analysis': {
                    'results': results,
                    'best_match': best_match,
                    'total_matches': len(results),
                    'skills_analyzed': len(skills)
                },
                'live_jobs': live_jobs,
                'course_recommendations': course_recommendations
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            print(f"Error in job analysis: {str(e)}")  # Debug print
            return JsonResponse({
                'status': 'error',
                'error': str(e),
                'message': 'An error occurred while analyzing skills'
            }, status=500)
    
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

def get_trending_courses():
    """
    Uses the Gemini API to get trending course recommendations.
    """
    model = genai.GenerativeModel('gemini-1.5-pro')

    prompt_template = """
**Role:** You are an AI Career Advisor Assistant specializing in identifying relevant online learning resources.

**Task:** Your primary goal is to recommend specific, high-quality trending online courses from reputable platforms (like Coursera, Udemy, edX, LinkedIn Learning, etc.) for the most in-demand tech skills in 2024.

**Output Requirements:**
* Provide your response as a single, valid JSON object.
* The main key of this object should be `trending_courses`.
* Group courses by skill categories (e.g., 'AI/ML', 'Web Development', 'Cloud Computing', 'Data Science', 'Cybersecurity').
* For each category, provide EXACTLY 3 trending courses.
* Each course object must have:
    * `course_title`: The official title of the course (string)
    * `platform`: The name of the platform hosting the course (string)
    * `url`: The direct URL link to the course page (string)
    * `level`: The difficulty level (string)
    * `description`: A brief, one-sentence description
    * `popularity_reason`: Why this course is trending (string)

Please provide trending courses that are currently popular in 2024.
"""

    try:
        response = model.generate_content(prompt_template)
        
        if not response or not response.text:
            error_msg = "Received empty response from Gemini API"
            print(error_msg)
            return {"error": error_msg}
            
        raw_text = response.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].strip()
        
        try:
            recommendations = json.loads(raw_text)
            return recommendations
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse Gemini API response as JSON: {str(e)}"
            print(error_msg)
            return {"error": error_msg}

    except Exception as e:
        error_msg = f"Error calling Gemini API for trending courses: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

def trending_courses(request):
    """
    View to display trending courses across different tech categories.
    """
    if request.method == 'GET':
        trending_recommendations = get_trending_courses()
        
        if 'error' in trending_recommendations:
            messages.error(request, trending_recommendations['error'])
            return render(request, 'trending_courses.html', {
                'courses': {},
                'error': trending_recommendations['error']
            })
            
        return render(request, 'trending_courses.html', {
            'courses': trending_recommendations.get('trending_courses', {})
        })

    return render(request, 'trending_courses.html', {'courses': {}})

def test_gemini_api():
    """
    Test function to verify if the Gemini API key is valid
    Returns a tuple of (is_valid: bool, message: str)
    """
    try:
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Create a simple model instance
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Try a simple generation
        response = model.generate_content("Hello, this is a test message to verify API key.")
        
        if response and response.text:
            return True, "API key is valid and working correctly."
        else:
            return False, "API key seems valid but received empty response."
            
    except Exception as e:
        error_message = str(e)
        if "API key not found" in error_message or "invalid api key" in error_message.lower():
            return False, f"Invalid API key: {error_message}"
        else:
            return False, f"Error testing API key: {error_message}"

def test_resume_analysis(request):
    """
    Test endpoint to verify each component of resume analysis
    """
    test_results = {
        'components': {
            'file_processing': {
                'pdf_support': 'PyPDF2' in globals(),
                'docx_support': 'docx' in globals()
            },
            'ai_integration': {
                'gemini_configured': bool(settings.GEMINI_API_KEY),
                'gemini_key_valid': settings.GEMINI_API_KEY != 'AIzaSyCphmUSSXd-TpUbu2q2pBJTV9bsV1wmM4Q'
            },
            'database': {
                'job_markets_count': JobMarket.objects.count(),
                'sample_job_titles': list(JobMarket.objects.values_list('title', flat=True))
            },
            'skill_detection': {
                'total_skills_monitored': len(technical_skills),
                'sample_skills': list(technical_skills)[:10]
            }
        },
        'status': 'operational'
    }
    
    # Test Gemini API
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content("Test connection")
        test_results['components']['ai_integration']['gemini_test_response'] = 'success'
    except Exception as e:
        test_results['components']['ai_integration']['gemini_test_response'] = f'error: {str(e)}'
        test_results['status'] = 'partial'
    
    # Overall status check
    if not test_results['components']['database']['job_markets_count']:
        test_results['status'] = 'error'
        test_results['error'] = 'No job markets found in database'
    elif not test_results['components']['ai_integration']['gemini_key_valid']:
        test_results['status'] = 'error'
        test_results['error'] = 'Invalid Gemini API key'
    
    return JsonResponse(test_results)

def test_skill_extraction(request):
    """
    Test endpoint to verify skill extraction from sample text
    """
    if request.method == 'POST':
        try:
            # Get the text from the request
            text = request.POST.get('text', '')
            if not text:
                return JsonResponse({'error': 'No text provided'}, status=400)

            # Convert to lowercase for case-insensitive matching
            text = text.lower()
            
            # Define technical skills (same as in resume_upload)
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
            
            found_skills = []
            skill_locations = {}  # To store where each skill was found
            
            # Look for skills with word boundaries
            for skill in technical_skills:
                skill_pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                matches = list(re.finditer(skill_pattern, text))
                if matches:
                    found_skills.append(skill)
                    # Store the character positions where this skill was found
                    skill_locations[skill] = [(m.start(), m.end()) for m in matches]
            
            # Check for skill variations
            skill_variations = {
                'js': 'javascript',
                'node': 'node.js',
                'react.js': 'react',
                'vue.js': 'vue',
                'postgres': 'postgresql',
                'ml': 'machine learning',
                'ai': 'artificial intelligence',
                'cv': 'computer vision'
            }
            
            for variation, main_skill in skill_variations.items():
                if main_skill not in found_skills:  # Only check if main skill wasn't found
                    variation_pattern = r'\b' + re.escape(variation.lower()) + r'\b'
                    matches = list(re.finditer(variation_pattern, text))
                    if matches:
                        found_skills.append(main_skill)
                        # Store the character positions where this variation was found
                        skill_locations[f"{main_skill} (as '{variation}')"] = [(m.start(), m.end()) for m in matches]
            
            # Sort and remove duplicates
            found_skills = sorted(list(set(found_skills)))
            
            return JsonResponse({
                'found_skills': found_skills,
                'skill_locations': skill_locations,
                'text_analyzed': text[:1000],  # Return first 1000 chars of analyzed text
                'total_skills_found': len(found_skills)
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def save_job(request):
    """
    View for saving/unsaving a job.
    Handles both saving and removing jobs from the user's profile.
    """
    if request.method == 'POST':
        try:
            job_data = json.loads(request.body)
            
            # Get or create profile
            profile = request.user.profile
            
            # Check if job exists by URL
            job_url = job_data.get('url', '')
            job_exists = any(job.get('url') == job_url for job in profile.get_saved_jobs())
            
            if job_exists:
                # If job exists, remove it (unsave)
                success = profile.remove_job(job_url)
                if success:
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Job removed from saved jobs',
                        'action': 'unsaved'
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Failed to remove job'
                    })
            else:
                # If job doesn't exist, save it
                success = profile.save_job(job_data)
                if success:
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Job saved successfully',
                        'action': 'saved'
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Job already saved'
                    })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

@login_required
def saved_jobs(request):
    saved_jobs = SavedJob.objects.filter(user=request.user).order_by('-saved_at')
    return render(request, 'jobs/saved_jobs.html', {'saved_jobs': saved_jobs}) 