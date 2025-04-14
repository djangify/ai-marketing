# assets/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json
import os
import uuid
from .models import Asset, AssetProcessingJob
from projects.models import Project
from .utils import create_asset_processing_job, determine_process_function
from django.contrib import messages


@login_required
def asset_list(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    assets = project.client_assets.all().order_by('-updated_at')
    
    # Calculate total token count for usage stats
    total_token_count = sum(asset.token_count or 0 for asset in assets)
    max_tokens = settings.MAX_TOKENS_ASSETS
    
    # Add usage stats to response headers
    usage_stats = {
        'totalTokenCount': total_token_count,
        'maxTokens': max_tokens,
    }
    
    context = {
        'assets': assets,
        'project': project,
    }
    
    response = render(request, 'assets/asset_list.html', context)
    response['X-Usage-Stats'] = json.dumps(usage_stats)
    return response


@login_required
@require_POST
def asset_upload(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            uploaded_files = request.FILES.getlist('files')
            results = []
            
            print(f"Received {len(uploaded_files)} files for upload")
            
            for file in uploaded_files:
                # Generate a unique filename to avoid collisions
                filename = f"{project_id}/{uuid.uuid4()}_{file.name}"
                
                # Check for duplicate file names
                existing_assets = Asset.objects.filter(project=project, title=file.name)
                
                # If this is a duplicate, let the client know
                if existing_assets.exists() and not request.POST.get('overwrite'):
                    return JsonResponse({
                        'success': False, 
                        'error': 'duplicate', 
                        'duplicate': True,
                        'filename': file.name,
                        'message': f"File '{file.name}' already exists. Do you want to overwrite it?"
                    })
                
                # If overwrite is confirmed, delete the existing assets
                if existing_assets.exists() and request.POST.get('overwrite') == 'true':
                    for asset in existing_assets:
                        # Delete file from storage
                        old_path = os.path.join(settings.MEDIA_ROOT, asset.file_name)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                        asset.delete()
                
                # Determine file type
                file_type = determine_file_type(file.name, file.content_type)
                
                # Save file in media directory
                file_path = os.path.join(settings.MEDIA_ROOT, filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                
                # Create file URL
                file_url = f"{settings.MEDIA_URL}{filename}"
                
                # Initialize content and token_count
                content = ""
                token_count = 0
                
                # Process files immediately for content when possible
                try:
                    process_func = determine_process_function(file_type, file.content_type)
                    content, token_count = process_func(file_path)
                except Exception as e:
                    print(f"Error processing file: {e}")
                    content = ""
                    token_count = 0
                
                print(f"About to create asset with title: {file.name}")
                
                # Create asset in database
                asset = Asset.objects.create(
                    project=project,
                    title=file.name,
                    file_name=filename,
                    file_url=file_url,
                    file_type=file_type,
                    mime_type=file.content_type,
                    size=file.size,
                    content=content,
                    token_count=token_count,
                )
                
                # Create processing job for audio and video files
                if file_type in ['audio', 'video']:
                    create_asset_processing_job(asset, project)
                    print(f"Created processing job for asset: {asset.id}")
                else:
                    # For text files, mark as completed
                    AssetProcessingJob.objects.create(
                        asset=asset,
                        project=project,
                        status='completed',
                        attempts=0,
                    )
                    print(f"Created completed processing job for asset: {asset.id}")
                
                results.append({
                    'id': str(asset.id),
                    'name': asset.title,
                    'url': asset.file_url,
                })
            
            # Add success message for the request object
            messages.success(request, "Files uploaded successfully")
            
            return JsonResponse({'success': True, 'files': results})
        
        except Exception as e:
            print(f"Exception during file upload: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    # Handle non-AJAX requests
    messages.error(request, "Direct form submission not supported. Please use the upload interface.")
    return redirect('projects:project_detail', project_id=project_id, tab='upload')


@login_required
@csrf_exempt
def asset_delete(request, project_id):
    if request.method == 'DELETE' or (request.method == 'POST' and request.POST.get('_method') == 'DELETE'):
        asset_id = request.GET.get('asset_id')
        if not asset_id:
            return JsonResponse({'success': False, 'error': 'Asset ID is required'}, status=400)
        
        project = get_object_or_404(Project, id=project_id, user=request.user)
        try:
            asset = get_object_or_404(Asset, id=asset_id, project=project)
            
            # Delete the file from storage
            file_path = os.path.join(settings.MEDIA_ROOT, asset.file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Delete the asset record (cascade will delete the processing job)
            asset.delete()
            
            # Add success message
            messages.success(request, "Asset deleted successfully")
            
            # For AJAX requests, still return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Asset deleted successfully'})
            
            # For regular requests, redirect to project detail page
            return redirect('projects:project_detail', project_id=project.id, tab='upload')
        
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
            messages.error(request, f"Error deleting asset: {str(e)}")
            return redirect('projects:project_detail', project_id=project.id, tab='upload')
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


@login_required
def asset_detail(request, project_id, asset_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    asset = get_object_or_404(Asset, id=asset_id, project=project)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': str(asset.id),
            'title': asset.title,
            'fileName': asset.file_name,
            'fileUrl': asset.file_url,
            'fileType': asset.file_type,
            'mimeType': asset.mime_type,
            'size': asset.size,
            'content': asset.content,
            'tokenCount': asset.token_count,
            'createdAt': asset.created_at.isoformat(),
            'updatedAt': asset.updated_at.isoformat(),
        })
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

@login_required
def asset_processing_jobs(request, project_id):
    """Get all asset processing jobs for a project"""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    jobs = AssetProcessingJob.objects.filter(project=project)
    
    results = []
    for job in jobs:
        results.append({
            'id': str(job.id),
            'assetId': str(job.asset.id),
            'status': job.status,
            'attempts': job.attempts,
            'errorMessage': job.error_message,
            'createdAt': job.created_at.isoformat(),
            'updatedAt': job.updated_at.isoformat(),
            'lastHeartBeat': job.last_heart_beat.isoformat(),
        })
    
    return JsonResponse(results, safe=False)

def determine_file_type(filename, mime_type):
    """Determine the file type based on filename and MIME type"""
    if mime_type.startswith('video/'):
        return 'video'
    elif mime_type.startswith('audio/'):
        return 'audio'
    elif mime_type == 'text/plain':
        return 'text'
    elif mime_type == 'text/markdown':
        return 'markdown'
    elif mime_type == 'application/pdf':
        return 'pdf'
    else:
        # Try to determine based on file extension
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.mp4', '.mov', '.avi', '.wmv']:
            return 'video'
        elif ext in ['.mp3', '.wav', '.ogg', '.m4a']:
            return 'audio'
        elif ext == '.md':
            return 'markdown'
        elif ext == '.txt':
            return 'text'
        elif ext == '.pdf':
            return 'pdf'
        return 'other'
    
@login_required
def all_assets(request):
    # Get all projects for the user
    projects = Project.objects.filter(user=request.user)
    
    # Get all assets across all projects
    assets = Asset.objects.filter(project__user=request.user).order_by('-updated_at')
    
    # Calculate total token count for usage stats
    total_token_count = sum(asset.token_count or 0 for asset in assets)
    max_tokens = settings.MAX_TOKENS_ASSETS
    
    # Add usage stats to response headers
    usage_stats = {
        'totalTokenCount': total_token_count,
        'maxTokens': max_tokens,
    }
    
    context = {
        'assets': assets,
        'project': None,  # No specific project
        'all_projects': True,
    }
    
    response = render(request, 'assets/all_assets.html', context)
    response['X-Usage-Stats'] = json.dumps(usage_stats)
    return response