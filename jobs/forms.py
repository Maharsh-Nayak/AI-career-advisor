from django import forms
from .models import NetworkingGoal

class ResumeUploadForm(forms.Form):
    resume = forms.FileField(
        label='Upload Resume', 
        help_text='Supported formats: PDF, DOCX',
        widget=forms.FileInput(attrs={'class': 'form-control-file'})
    )
    
    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:
            file_ext = resume.name.split('.')[-1].lower()
            if file_ext not in ['pdf', 'docx']:
                raise forms.ValidationError('File type not supported. Please upload a PDF or DOCX file.')
        return resume

class NetworkingGoalForm(forms.ModelForm):
    goal_text = forms.CharField(
        label="What's your networking goal?",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'E.g., "I want to connect with mentors in data science and product managers in gaming industry."'
        })
    )
    
    class Meta:
        model = NetworkingGoal
        fields = ['goal_text'] 