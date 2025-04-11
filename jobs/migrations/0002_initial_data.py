from django.db import migrations

def populate_job_market(apps, schema_editor):
    JobMarket = apps.get_model('jobs', 'JobMarket')
    
    job_market_data = {
        "software developer": ["python", "git", "docker", "javascript", "sql", "aws", "react", "node.js"],
        "data analyst": ["sql", "excel", "python", "tableau", "power bi", "r", "statistics", "machine learning"],
        "web designer": ["html", "css", "javascript", "figma", "photoshop", "ui/ux", "responsive design"],
        "devops engineer": ["docker", "kubernetes", "aws", "ci/cd", "linux", "terraform", "ansible"],
        "machine learning engineer": ["python", "tensorflow", "pytorch", "scikit-learn", "nlp", "computer vision", "data science"]
    }
    
    for title, skills in job_market_data.items():
        JobMarket.objects.create(title=title, required_skills=skills)

class Migration(migrations.Migration):
    dependencies = [
        ('jobs', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_job_market),
    ] 