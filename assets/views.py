# assets/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json
import os
from django.urls import reverse
import uuid
from .models import Asset, AssetProcessingJob
from projects.models import Project
from .utils import create_asset_processing_job, determine_process_function
from django.contrib import messages
from subscriptions.utils import subscription_required


@login_required
@subscription_required
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
@subscription_required
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
                
                # If this is a duplicate, let the client know, but only stop if it's a single file upload
                if existing_assets.exists() and not request.POST.get('overwrite'):
                # If we're uploading multiple files, we'll handle duplicates individually
                    if len(uploaded_files) == 1:
                        return JsonResponse({
                            'success': False, 
                            'error': 'duplicate', 
                            'duplicate': True,
                            'filename': file.name,
                            'message': f"File '{file.name}' already exists. Do you want to overwrite it?"
                        })
                # For multiple files, just skip this one if not overwriting
                    continue
                
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
                    print(f"File processed successfully, original token count: {token_count}")
                    
                    # First store the token count before sanitization
                    original_token_count = token_count
                    
                    # Now sanitize content for database storage
                    sanitized_content = sanitize_content(content) if content else ""
                    print(f"Content sanitized for database storage")
                    
                    # Create asset with sanitized content but preserve original token count
                    try:
                        asset = Asset.objects.create(
                            project=project,
                            title=file.name,
                            file_name=filename,
                            file_url=file_url,
                            file_type=file_type,
                            mime_type=file.content_type,
                            size=file.size,
                            content=sanitized_content,
                            token_count=original_token_count,  # Use original token count even if content is sanitized
                        )
                        print(f"Asset created successfully with token count: {original_token_count}")
                    except Exception as db_error:
                        print(f"Database error creating asset with sanitized content: {db_error}")
                        # If even sanitized content fails, create with empty content but keep token count
                        asset = Asset.objects.create(
                            project=project,
                            title=file.name,
                            file_name=filename,
                            file_url=file_url,
                            file_type=file_type,
                            mime_type=file.content_type,
                            size=file.size,
                            content="[Content not available due to encoding issues]",
                            token_count=original_token_count,  # Still use original token count
                        )
                        print(f"Created asset with placeholder content but preserved token count: {original_token_count}")
                    
                except Exception as process_error:
                    print(f"Error during file processing: {process_error}")
                    # Create asset with no content but still try to estimate token count from file size
                    estimated_token_count = max(1, int(file.size / 4))  # Rough estimate: ~4 bytes per token
                    print(f"Creating asset with estimated token count based on file size: {estimated_token_count}")
                    
                    asset = Asset.objects.create(
                        project=project,
                        title=file.name,
                        file_name=filename,
                        file_url=file_url,
                        file_type=file_type,
                        mime_type=file.content_type,
                        size=file.size,
                        content="[File could not be processed. Original file preserved.]",
                        token_count=estimated_token_count,
                    )
                except Exception as db_error:
                    print(f"Database error creating asset: {db_error}")
                    # Fallback - try creating with empty content if there was a database error
                    asset = Asset.objects.create(
                        project=project,
                        title=file.name,
                        file_name=filename,
                        file_url=file_url,
                        file_type=file_type,
                        mime_type=file.content_type,
                        size=file.size,
                        content="[Content not available due to encoding issues]",
                        token_count=0,
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


def sanitize_content(content):
    """Sanitize content to handle special characters and encoding issues"""
    if not content:
        return ""
    
    # First try to normalize Unicode
    try:
        import unicodedata
        content = unicodedata.normalize('NFKD', content)
    except Exception as e:
        print(f"Unicode normalization error: {e}")
    
    # Remove or replace problematic characters that cause MySQL encoding issues
    try:
        # More aggressive sanitization for production MySQL
        # Replace any character that's not ASCII or basic Unicode with a space
        import re
        # This regex keeps only ASCII characters, common Unicode, and basic punctuation
        content = re.sub(r'[^\x00-\x7F\u2000-\u206F\u2E00-\u2E7F\s]', ' ', content)
    except Exception as e:
        print(f"Regex sanitization error: {e}")
        
    # As a last resort, encode and decode with strict error handling
    try:
        if isinstance(content, str):
            content = content.encode('ascii', errors='ignore').decode('ascii', errors='ignore')
    except Exception as e:
        print(f"ASCII encode/decode error: {e}")
    
    return content


@login_required
def asset_delete(request, project_id, asset_id):
    """Delete an asset (with confirmation page)"""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    asset = get_object_or_404(Asset, id=asset_id, project=project)

    if request.method == 'POST':
        try:
            # Delete the file from storage
            file_path = os.path.join(settings.MEDIA_ROOT, asset.file_name)
            if os.path.exists(file_path):
                os.remove(file_path)

            # Delete the asset record
            asset.delete()

            messages.success(request, "Asset deleted successfully")
            # Redirect back to project detail with ?tab=upload
            url = reverse('projects:project_detail', kwargs={'project_id': project.id})
            return redirect(f"{url}?tab=upload")

        except Exception as e:
            messages.error(request, f"Error deleting asset: {str(e)}")
            url = reverse('projects:project_detail', kwargs={'project_id': project.id})
            return redirect(f"{url}?tab=upload")

    # GET request – show confirmation page
    return render(request, 'assets/asset_confirm_delete.html', {
        'project': project,
        'asset': asset,
    })


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
@subscription_required
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