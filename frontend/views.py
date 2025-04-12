from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
import requests
from jobs.utils import extract_keywords, match_suggestions, generate_linkedin_search_url, generate_linkedin_profiles_with_gemini

def home(request):
    return render(request, 'index.html')

@csrf_exempt
def networking_analysis(request):
    if request.method == 'GET':
        return render(request, 'networking_analysis.html')
    
    if request.method == 'POST':
        try:
            # Get networking goal from form
            networking_goal = request.POST.get('networking_goal', '')
            
            if not networking_goal:
                return JsonResponse({'error': 'No networking goal provided'}, status=400)
            
            # Extract keywords from the goal text
            keywords = extract_keywords(networking_goal)
            
            # Get suggestions based on the keywords
            suggestions = match_suggestions(keywords)
            
            # Use Gemini API to generate optimized LinkedIn profile recommendations
            linkedin_profiles = generate_linkedin_profiles_with_gemini(networking_goal, keywords)
            
            # Store the data in the database if user is authenticated
            if request.user.is_authenticated:
                from jobs.models import NetworkingGoal
                
                # Save the networking goal and analysis
                goal_obj = NetworkingGoal.objects.create(
                    user=request.user,
                    goal_text=networking_goal,
                    extracted_keywords={"keywords": keywords},
                    industries=suggestions['relevant_industries'],
                    companies=suggestions['example_companies'],
                    roles=suggestions['relevant_role_types']
                )
            
            # Add LinkedIn profiles to the response
            suggestions['linkedin_profiles'] = linkedin_profiles
            
            return JsonResponse({
                'status': 'success',
                'analysis': suggestions
            })
            
        except Exception as e:
            print(f"Error: {str(e)}")
            # Create a simple fallback response
            fallback_analysis = {
                "relevant_industries": [
                    {
                        "name": "Technology",
                        "reason": "Default recommendation based on common trends"
                    }
                ],
                "example_companies": [
                    {
                        "name": "Microsoft",
                        "reason": "Major technology company with diverse roles"
                    }
                ],
                "relevant_role_types": [
                    {
                        "title": "Data Analyst",
                        "reason": "Growing field with opportunities across industries"
                    }
                ]
            }
            
            return JsonResponse({
                'status': 'success',
                'analysis': fallback_analysis
            })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405) 