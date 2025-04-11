from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import JobMarket
from .services import JobFetcher
from .serializers import JobMarketSerializer
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

def index(request):
    return render(request, 'index.html')

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
            
            # Fetch live jobs
            search_keyword = skills[0]
            live_jobs = JobFetcher.fetch_all_jobs(search_keyword)
            
            return JsonResponse({
                'analysis': results,
                'live_jobs': live_jobs
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405) 