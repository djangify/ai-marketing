from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
import threading
import json

from projects.models import Project, GeneratedContent
from .models import ContentGenerationJob
from .services import GenerationManager

generation_manager = GenerationManager()

@login_required
def generate_content(request, project_id):
    """View for the content generation page"""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    # Check for existing generation job
    active_job = ContentGenerationJob.objects.filter(
        project=project, 
        status__in=['pending', 'in_progress']
    ).first()
    
    # Get generated content
    generated_contents = project.generated_contents.all().order_by('order')
    
    context = {
        'project': project,
        'active_job': active_job,
        'generated_contents': generated_contents,
    }
    
    return render(request, 'content_generation/generate.html', context)

@login_required
def generation_status(request, project_id):
    """View for the generation status"""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    # Check for active job
    job = ContentGenerationJob.objects.filter(
        project=project, 
        status__in=['pending', 'in_progress']
    ).first()
    
    # Get generated content
    generated_contents = project.generated_contents.all().order_by('order')
    
    context = {
        'project': project,
        'job': job,
        'generated_contents': generated_contents,
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        format_type = request.GET.get('format', 'html')
        if format_type == 'json':
            is_generating = bool(job)
            response_data = {
                'isGenerating': is_generating,
                'status': job.status if job else None,
                'generatedCount': job.prompts_completed if job else 0,
                'totalPrompts': job.prompts_total if job else 0,
                'errorMessage': job.error_message if job and job.error_message else None,
                'completedAt': job.completed_at.isoformat() if job and job.completed_at else None
            }
            return JsonResponse(response_data)
    
    # Regular HTML request
    return render(request, 'content_generation/status.html', context)

@login_required
def update_generated_content(request, content_id):
    """View for updating generated content"""
    content = get_object_or_404(GeneratedContent, id=content_id)
    project = content.project
    
    # Ensure user has permission
    if project.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    if request.method == 'POST':
        result = request.POST.get('result')
        
        if not result:
            return JsonResponse({'error': 'Content cannot be empty'}, status=400)
        
        content.result = result
        content.save()
        
        return redirect('projects:project_detail', project_id=project.id, tab='generate')
    
    context = {
        'project': project,
        'content': content,
    }
    
    return render(request, 'content_generation/edit_content.html', context)

# AJAX endpoints
@login_required
@require_POST
def start_generation(request, project_id):
    """AJAX endpoint to start content generation"""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    # Check for existing generation job
    existing_job = ContentGenerationJob.objects.filter(
        project=project, 
        status__in=['pending', 'in_progress']
    ).first()
    
    if existing_job:
        return JsonResponse({
            'success': False,
            'error': 'A generation job is already in progress'
        }, status=400)
    
    try:
        # Create new generation job
        job = generation_manager.start_generation_job(project_id, request.user)
        
        # Run generation in background thread
        def run_generation():
            generation_manager.process_generation_job(job.id)
        
        threading.Thread(target=run_generation).start()
        
        return JsonResponse({
            'success': True,
            'job_id': str(job.id),
            'status': job.status
        })
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)

@login_required
def get_generation_status(request, project_id):
    """AJAX endpoint to get the status of content generation"""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    # Get the latest job for this project
    job = ContentGenerationJob.objects.filter(project=project).order_by('-started_at').first()
    
    if not job:
        return JsonResponse({
            'is_generating': False,
            'status': None,
            'progress': 0,
            'error': None
        })
    
    # Calculate progress
    progress = 0
    if job.prompts_total > 0:
        progress = int((job.prompts_completed / job.prompts_total) * 100)
    
    # Get result IDs if job is completed
    result_ids = []
    if job.status == 'completed':
        contents = GeneratedContent.objects.filter(project=project).order_by('order')
        result_ids = [str(content.id) for content in contents]
    
    return JsonResponse({
        'is_generating': job.status in ['pending', 'in_progress'],
        'status': job.status,
        'progress': progress,
        'total_prompts': job.prompts_total,
        'completed_prompts': job.prompts_completed,
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'error': job.error_message,
        'result_ids': result_ids
    })

@login_required
@require_POST
def cancel_generation(request, project_id):
    """AJAX endpoint to cancel a running generation job"""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    job = ContentGenerationJob.objects.filter(
        project=project, 
        status__in=['pending', 'in_progress']
    ).first()
    
    if not job:
        return JsonResponse({
            'success': False,
            'error': 'No active generation job found'
        }, status=404)
    
    # Mark job as canceled
    job.status = 'canceled'
    job.completed_at = timezone.now()
    job.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Generation job canceled'
    })

@login_required
@csrf_exempt
@require_http_methods(["PATCH"])
def edit_generated_content(request, content_id):
    """AJAX endpoint to update generated content"""
    content = get_object_or_404(GeneratedContent, id=content_id)
    project = content.project
    
    # Ensure user has permission
    if project.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        result = data.get('result')
        
        if not result:
            return JsonResponse({'error': 'Content cannot be empty'}, status=400)
        
        content.result = result
        content.save()
        
        return JsonResponse({
            'id': str(content.id),
            'name': content.name,
            'result': content.result,
            'order': content.order
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)