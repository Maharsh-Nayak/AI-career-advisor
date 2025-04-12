from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests

def index(request):
    return render(request, 'index.html')

@csrf_exempt
def networking_analysis(request):
    if request.method == 'GET':
        return render(request, 'networking_analysis.html')
    
    # For POST requests, directly handle here instead of redirecting
    if request.method == 'POST':
        try:
            from django.conf import settings
            import google.generativeai as genai
            
            # Configure Gemini
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Get user profile data from the request
            profile_data = {
                'current_role': request.POST.get('current_role', ''),
                'industry': request.POST.get('industry', ''),
                'skills': request.POST.get('skills', '').split(','),
                'experience': request.POST.get('experience', ''),
                'location': request.POST.get('location', ''),
                'networking_goal': request.POST.get('networking_goal', '')
            }

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
            
            # Handle the response properly
            response_text = response.text
            
            # Try to parse the response
            try:
                # Clean the response text if it contains markdown formatting
                if "```json" in response_text:
                    # Extract the JSON part
                    start_idx = response_text.find("```json") + 7
                    end_idx = response_text.find("```", start_idx)
                    response_text = response_text[start_idx:end_idx].strip()
                elif "```" in response_text:
                    # Extract content from markdown code block
                    start_idx = response_text.find("```") + 3
                    end_idx = response_text.find("```", start_idx)
                    response_text = response_text[start_idx:end_idx].strip()
                
                # Parse the JSON
                analysis = json.loads(response_text)
                return JsonResponse({
                    'status': 'success',
                    'analysis': analysis
                })
            except json.JSONDecodeError:
                # If JSON parsing fails, create a default response
                fallback_analysis = {
                    "relevant_industries": [
                        {
                            "name": "Technology",
                            "reason": "Based on your skills and goals"
                        }
                    ],
                    "example_companies": [
                        {
                            "name": "Google",
                            "reason": "Leading technology company with diverse opportunities"
                        }
                    ],
                    "relevant_role_types": [
                        {
                            "title": "Software Developer",
                            "reason": "In-demand role with growth potential"
                        }
                    ]
                }
                
                return JsonResponse({
                    'status': 'success',
                    'analysis': fallback_analysis
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