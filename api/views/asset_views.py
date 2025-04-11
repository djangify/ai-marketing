from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from projects.models import Asset, AssetProcessingJob, Project
from ..serializers import AssetSerializer, AssetProcessingJobSerializer
from django.utils import timezone
from ..permissions import ServerAPIPermission

# ViewSets
class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    permission_classes = [IsAuthenticated]

class AssetProcessingJobViewSet(viewsets.ModelViewSet):
    queryset = AssetProcessingJob.objects.all()
    serializer_class = AssetProcessingJobSerializer
    permission_classes = [ServerAPIPermission]

# API Views
@api_view(['GET', 'PATCH'])
@permission_classes([ServerAPIPermission])
def asset_detail(request):
    """
    Get or update asset details
    """
    asset_id = request.GET.get('assetId')
    if not asset_id:
        return Response({"error": "Missing assetId parameter"}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        asset = get_object_or_404(Asset, id=asset_id)
        
        if request.method == 'GET':
            serializer = AssetSerializer(asset)
            return Response(serializer.data)
            
        elif request.method == 'PATCH':
            serializer = AssetSerializer(asset, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"success": True})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'PATCH'])
@permission_classes([ServerAPIPermission])
def asset_processing_job_list(request):
    """
    Get non-terminal asset processing jobs or update a job
    """
    if request.method == 'GET':
        # Fetch jobs not in terminal state
        non_terminal_states = ['created', 'failed', 'in_progress']
        available_jobs = AssetProcessingJob.objects.filter(status__in=non_terminal_states)
        serializer = AssetProcessingJobSerializer(available_jobs, many=True)
        return Response(serializer.data)
        
    elif request.method == 'PATCH':
        job_id = request.GET.get('jobId')
        if not job_id:
            return Response({"error": "Missing jobId parameter"}, status=status.HTTP_400_BAD_REQUEST)
            
        job = get_object_or_404(AssetProcessingJob, id=job_id)
        
        # Update job with partial data
        serializer = AssetProcessingJobSerializer(job, data=request.data, partial=True)
        if serializer.is_valid():
            # If last_heart_beat is in the data, convert it to datetime
            if 'lastHeartBeat' in request.data:
                # Convert the string to a datetime
                heart_beat_time = timezone.datetime.fromisoformat(request.data['lastHeartBeat'].replace('Z', '+00:00'))
                job.last_heart_beat = heart_beat_time
            
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def asset_processing_job_project(request, project_id):
    """
    Get asset processing jobs for a specific project
    """
    try:
        project = get_object_or_404(Project, id=project_id, user=request.user)
        jobs = AssetProcessingJob.objects.filter(project=project)
        serializer = AssetProcessingJobSerializer(jobs, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload(request):
    """
    Handle file uploads to local storage
    """
    try:
        from ..utils import CPanelFileStorage
        from projects.models import Asset, AssetProcessingJob
        
        project_id = request.POST.get('projectId')
        if not project_id:
            return Response({"error": "Project ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        project = get_object_or_404(Project, id=project_id, user=request.user)
        files = request.FILES.getlist('files')
        
        if not files:
            return Response({"error": "No files provided"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Initialize storage service
        storage = CPanelFileStorage()
        
        uploaded_assets = []
        for file_obj in files:
            # Determine file type
            file_name = file_obj.name
            content_type = file_obj.content_type
            
            if content_type.startswith('video/'):
                file_type = 'video'
            elif content_type.startswith('audio/'):
                file_type = 'audio'
            elif content_type == 'text/plain':
                file_type = 'text'
            elif content_type == 'text/markdown':
                file_type = 'markdown'
            else:
                file_type = 'other'
                
            # Save file
            file_data = storage.save_file(file_obj, project_id)
            
            # Create asset
            asset = Asset.objects.create(
                project=project,
                title=file_name,
                file_name=file_data['filename'],
                file_url=file_data['url'],
                file_type=file_type,
                mime_type=content_type,
                size=file_data['size']
            )
            
            # Create processing job
            job = AssetProcessingJob.objects.create(
                asset=asset,
                project=project,
                status='created'
            )
            
            uploaded_assets.append({
                'id': str(asset.id),
                'title': asset.title,
                'fileUrl': asset.file_url
            })
            
        return Response({
            'success': True,
            'assets': uploaded_assets
        })
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Add this to api/views/asset_views.py
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def asset_delete(request, project_id):
    """
    Delete an asset and its associated file
    """
    try:
        from ..utils import CPanelFileStorage
        
        asset_id = request.GET.get('assetId')
        if not asset_id:
            return Response({"error": "Asset ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        project = get_object_or_404(Project, id=project_id, user=request.user)
        asset = get_object_or_404(Asset, id=asset_id, project=project)
        
        # Delete file from storage
        storage = CPanelFileStorage()
        storage.delete_file(asset.file_name)
        
        # Delete asset from database
        asset.delete()
        
        return Response({"success": True, "message": "Asset deleted successfully"})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)