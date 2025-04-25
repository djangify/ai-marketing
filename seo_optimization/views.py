# seo_optimization/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages

from projects.models import Project, GeneratedContent
from seo_optimization.models import SEOAnalysis, KeywordTracking
from .utils import analyze_content_for_seo
import json
import os
import nltk
from subscriptions.utils import subscription_required


# Set up the NLTK data path 
nltk_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'nltk_data')
if nltk_path not in nltk.data.path:
    nltk.data.path.insert(0, nltk_path)
# First, prioritize nltk_data in the project directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_nltk_data = os.path.join(BASE_DIR, 'nltk_data')
if os.path.exists(project_nltk_data):
    nltk.data.path.insert(0, project_nltk_data)

# Then try the user's home directory (works in local environments)
home_nltk_data = os.path.expanduser('~/nltk_data')
if os.path.exists(home_nltk_data):
    nltk.data.path.append(home_nltk_data)

# Also check for system-wide nltk data (for cPanel and other environments)
for path in ['/usr/share/nltk_data', '/usr/local/share/nltk_data', '/usr/lib/nltk_data']:
    if os.path.exists(path):
        nltk.data.path.append(path)

# Ensure we have the needed NLTK resources (fail early if data is missing)
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError as e:
    print(f"NLTK Error: {e}")
    print("Run setup_nltk.py to download required NLTK data")


@login_required
@subscription_required
def analyze_content(request, content_id):
    """Analyze a single generated content for SEO"""
    content = get_object_or_404(GeneratedContent, id=content_id)
    project = content.project
    
    # Verify user has permission to access this content
    if project.user != request.user:
        messages.error(request, "You don't have permission to access this content.")
        return redirect('projects:project_list')
    
    # Check if analysis already exists
    try:
        analysis = SEOAnalysis.objects.get(content=content)
        # Return the existing analysis
        return render(request, 'seo_optimization/analysis_detail.html', {
            'content': content,
            'project': project,
            'analysis': analysis
        })
    except SEOAnalysis.DoesNotExist:
        # Perform SEO analysis
        try:
            seo_data = analyze_content_for_seo(content.result)
            
            # Save the analysis
            analysis = SEOAnalysis.objects.create(
                content=content,
                project=project,
                readability_score=seo_data['readability_score'],
                keyword_density=seo_data['keyword_density'],
                suggested_keywords=seo_data['suggested_keywords'],
                meta_description=seo_data['meta_description'],
                seo_score=seo_data['seo_score'],
                improvement_suggestions=seo_data['improvement_suggestions']
            )
            
            # Add keywords to tracking
            for keyword in seo_data['suggested_keywords'][:5]:  # Track top 5 keywords
                keyword_obj, created = KeywordTracking.objects.get_or_create(
                    user=request.user,
                    keyword=keyword
                )
                keyword_obj.projects.add(project)
                
                # Update relevance score based on keyword density
                if keyword in seo_data['keyword_density']:
                    density = seo_data['keyword_density'][keyword]
                    # Scale density to relevance score (max 10)
                    keyword_obj.relevance_score = min(10, density * 3)
                    keyword_obj.save()
            
            return render(request, 'seo_optimization/analysis_detail.html', {
                'content': content,
                'project': project,
                'analysis': analysis
            })
        except LookupError as e:
            # Handle NLTK resource errors gracefully
            error_message = f"NLTK data not found: {str(e)}"
            messages.error(request, error_message)
            messages.info(request, "Please run setup_nltk.py to download required NLTK data.")
            return redirect('projects:project_detail', project_id=project.id)
        except Exception as e:
            # Handle other errors
            error_message = f"Error analyzing content: {str(e)}"
            messages.error(request, error_message)
            return redirect('projects:project_detail', project_id=project.id)


@login_required
@subscription_required
def analysis_detail(request, analysis_id):
    """View a specific SEO analysis"""
    analysis = get_object_or_404(SEOAnalysis, id=analysis_id)
    
    # Verify user has permission
    if analysis.project.user != request.user:
        messages.error(request, "You don't have permission to access this analysis.")
        return redirect('projects:project_list')
    
    return render(request, 'seo_optimization/analysis_detail.html', {
        'content': analysis.content,
        'project': analysis.project,
        'analysis': analysis
    })


@login_required
@subscription_required
def project_analyses(request, project_id):
    """View all SEO analyses for a project"""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    analyses = SEOAnalysis.objects.filter(project=project).order_by('-created_at')
    
    return render(request, 'seo_optimization/project_analyses.html', {
        'project': project,
        'analyses': analyses
    })


@login_required
@subscription_required
def keyword_tracking(request):
    """View all tracked keywords for a user"""
    keywords = KeywordTracking.objects.filter(user=request.user).order_by('-relevance_score')
    
    return render(request, 'seo_optimization/keyword_tracking.html', {
        'keywords': keywords
    })


@require_POST
@login_required
def ajax_analyze_content(request):
    """AJAX endpoint to analyze content and return results"""
    try:
        data = json.loads(request.body)
        content_id = data.get('content_id')
        
        if not content_id:
            return JsonResponse({'error': 'Content ID is required'}, status=400)
        
        content = get_object_or_404(GeneratedContent, id=content_id)
        
        # Verify user has permission
        if content.project.user != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Check for existing analysis
        try:
            analysis = SEOAnalysis.objects.get(content=content)
            # If the content might have changed, re-analyze
            if data.get('force_reanalyze', False):
                seo_data = analyze_content_for_seo(content.result)
                
                # Update existing analysis
                analysis.readability_score = seo_data['readability_score']
                analysis.keyword_density = seo_data['keyword_density']
                analysis.suggested_keywords = seo_data['suggested_keywords']
                analysis.meta_description = seo_data['meta_description']
                analysis.seo_score = seo_data['seo_score']
                analysis.improvement_suggestions = seo_data['improvement_suggestions']
                analysis.save()
        except SEOAnalysis.DoesNotExist:
            # Perform new analysis
            seo_data = analyze_content_for_seo(content.result)
            
            # Create new analysis
            analysis = SEOAnalysis.objects.create(
                content=content,
                project=content.project,
                readability_score=seo_data['readability_score'],
                keyword_density=seo_data['keyword_density'],
                suggested_keywords=seo_data['suggested_keywords'],
                meta_description=seo_data['meta_description'],
                seo_score=seo_data['seo_score'],
                improvement_suggestions=seo_data['improvement_suggestions']
            )
            
            # Add keywords to tracking
            for keyword in seo_data['suggested_keywords'][:5]:  # Track top 5 keywords
                keyword_obj, created = KeywordTracking.objects.get_or_create(
                    user=request.user,
                    keyword=keyword
                )
                keyword_obj.projects.add(content.project)
                
                # Update relevance score based on keyword density
                if keyword in seo_data['keyword_density']:
                    density = seo_data['keyword_density'][keyword]
                    # Scale density to relevance score (max 10)
                    keyword_obj.relevance_score = min(10, density * 3)
                    keyword_obj.save()
        
        # Return analysis data
        return JsonResponse({
            'id': str(analysis.id),
            'readability_score': analysis.readability_score,
            'keyword_density': analysis.keyword_density,
            'suggested_keywords': analysis.suggested_keywords,
            'meta_description': analysis.meta_description,
            'seo_score': analysis.seo_score,
            'improvement_suggestions': analysis.improvement_suggestions,
            'content_id': str(content.id),
            'project_id': str(content.project.id)
        })
        
    except LookupError as e:
        # Handle NLTK resource errors
        return JsonResponse({'error': f"NLTK data not found: {str(e)}. Run setup_nltk.py to download the required data."}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@login_required
@subscription_required
def ajax_update_meta_description(request):
    """AJAX endpoint to update a meta description"""
    try:
        data = json.loads(request.body)
        analysis_id = data.get('analysis_id')
        meta_description = data.get('meta_description')
        
        if not analysis_id or not meta_description:
            return JsonResponse({'error': 'Analysis ID and meta description are required'}, status=400)
        
        analysis = get_object_or_404(SEOAnalysis, id=analysis_id)
        
        # Verify user has permission
        if analysis.project.user != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Update meta description
        analysis.meta_description = meta_description
        analysis.save()
        
        return JsonResponse({
            'success': True,
            'meta_description': analysis.meta_description
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@login_required
@subscription_required
def ajax_toggle_primary_keyword(request):
    """AJAX endpoint to toggle primary status of a keyword"""
    try:
        data = json.loads(request.body)
        keyword_id = data.get('keyword_id')
        
        if not keyword_id:
            return JsonResponse({'error': 'Keyword ID is required'}, status=400)
        
        keyword = get_object_or_404(KeywordTracking, id=keyword_id, user=request.user)
        
        # Toggle primary status
        keyword.is_primary = not keyword.is_primary
        keyword.save()
        
        return JsonResponse({
            'success': True,
            'is_primary': keyword.is_primary
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    