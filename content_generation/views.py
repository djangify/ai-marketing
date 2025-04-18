from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt

import openai
import threading
import json

from projects.models import Project, GeneratedContent
from .models import ContentGenerationJob, AIConfig
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

@login_required
@require_POST
def start_generation(request, project_id):
    """AJAX endpoint to start content generation"""
    print(f"Starting generation for project {project_id}")
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    # Check if this is an HTMX request
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    # Check for existing generation job
    existing_job = ContentGenerationJob.objects.filter(
        project=project, 
        status__in=['pending', 'in_progress']
    ).first()
    
    if existing_job:
        messages.error(request, 'A content generation job is already in progress')
        return JsonResponse({
            'success': False,
            'error': 'A generation job is already in progress'
        }, status=400)
    # Check if project has prompts
    prompts = project.project_prompts.all()
    prompt_count = prompts.count()
    print(f"Project has {prompt_count} prompts")
    if not prompts.exists():
        print("ERROR: No prompts found in this project")
        messages.error(request, 'No prompts found. Please add prompts before generating content.')
        return JsonResponse({
            'success': False,
            'error': 'No prompts found in this project'
        }, status=400)
    
    # Check if project has assets with content
    assets = project.client_assets.filter(content__isnull=False).exclude(content='')
    asset_count = assets.count()
    print(f"Project has {asset_count} assets with content")
    if asset_count == 0:
        print("Asset IDs in project:", list(project.client_assets.values_list('id', flat=True)))
        print("Assets without content:", project.client_assets.filter(content='').count())
        print("ERROR: No assets with content found in this project")
        messages.error(request, 'No content assets found. Please upload text files before generating content.')
        return JsonResponse({
            'success': False,
            'error': 'No assets with content found in this project'
        }, status=400)
    try:
        # Create new generation job
        job = generation_manager.start_generation_job(project_id, request.user)
        
        if not job:
            error_message = "Failed to create generation job"
            messages.error(request, error_message)
            return JsonResponse({
                'success': False,
                'error': error_message
            }, status=400)
        
        # Run generation in background thread
        def run_generation():
            try:
                if job and job.id:
                    generation_manager.process_generation_job(job.id)
                else:
                    print("Error: job or job.id is None in run_generation")
            except Exception as e:
                # Update job with error if generation fails
                if job:
                    job.status = 'failed'
                    job.error_message = str(e)
                    job.completed_at = timezone.now()
                    job.save()
                print(f"Error in generation thread: {str(e)}")
        
        thread = threading.Thread(target=run_generation)
        thread.daemon = True  # Make thread a daemon so it doesn't block server shutdown
        thread.start()
        
        messages.info(request, 'Content generation started. This may take a few minutes.')
        
        # Handle HTMX requests by returning the status template instead of JSON
        if is_htmx:
            print("HTMX request detected, returning status template")
            context = {
                'project': project,
                'job': job,
                'generated_contents': project.generated_contents.all().order_by('order'),
            }
            return render(request, 'content_generation/status.html', context)
        else:
            return JsonResponse({
                'success': True,
                'job_id': str(job.id),
                'status': job.status
            })
        
    except ValueError as e:
        error_message = str(e)
        messages.error(request, error_message)
        return JsonResponse({
            'success': False,
            'error': error_message
        }, status=400)
    
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        messages.error(request, error_message)
        return JsonResponse({
            'success': False,
            'error': error_message
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
        
        # Save previous content for logging
        previous_content = content.result
        
        # Update content
        content.result = result
        content.save()
        
        # Log success message
        print(f"Content {content_id} updated successfully by user {request.user.username}")
        
        return JsonResponse({
            'id': str(content.id),
            'name': content.name,
            'result': content.result,
            'order': content.order
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"Error updating content {content_id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    