from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
import threading

from projects.models import Project, GeneratedContent
from content_generation.models import ContentGenerationJob
from content_generation.services import GenerationManager
from api.serializers import GeneratedContentSerializer, ContentGenerationJobSerializer

# Initialize the generation manager
generation_manager = GenerationManager()

class ContentGenerationJobViewSet(viewsets.ModelViewSet):
    """ViewSet for the ContentGenerationJob model"""
    queryset = ContentGenerationJob.objects.all()
    serializer_class = ContentGenerationJobSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset to only include objects owned by the user"""
        user = self.request.user
        return ContentGenerationJob.objects.filter(user=user)

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def project_generation(request, project_id):
    """
    API endpoint for project generation jobs
    
    GET: Get generation job status
    POST: Start a new generation job
    DELETE: Cancel an existing job
    """
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    if request.method == 'GET':
        # Get the latest job for this project
        job = ContentGenerationJob.objects.filter(
            project=project
        ).order_by('-started_at').first()
        
        # Get generated content
        contents = GeneratedContent.objects.filter(
            project=project
        ).order_by('order')
        
        if not job:
            return Response({
                'is_generating': False,
                'status': None,
                'progress': 0,
                'generated_content': GeneratedContentSerializer(contents, many=True).data
            })
        
        # Calculate progress
        progress = 0
        if job.prompts_total > 0:
            progress = (job.prompts_completed / job.prompts_total) * 100
        
        serializer = ContentGenerationJobSerializer(job)
        return Response({
            'job': serializer.data,
            'is_generating': job.status in ['pending', 'in_progress'],
            'progress': progress,
            'generated_content': GeneratedContentSerializer(contents, many=True).data
        })
        
    elif request.method == 'POST':
        # Check for existing active job
        existing_job = ContentGenerationJob.objects.filter(
            project=project,
            status__in=['pending', 'in_progress']
        ).first()
        
        if existing_job:
            return Response({
                'error': 'A generation job is already in progress'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Start a new generation job
            job = generation_manager.start_generation_job(project_id, request.user)
            
            # Run generation in background thread
            def run_generation():
                generation_manager.process_generation_job(job.id)
            
            thread = threading.Thread(target=run_generation)
            thread.daemon = True
            thread.start()
            
            serializer = ContentGenerationJobSerializer(job)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                'error': 'An unexpected error occurred: ' + str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    elif request.method == 'DELETE':
        # Cancel an existing job
        job = ContentGenerationJob.objects.filter(
            project=project,
            status__in=['pending', 'in_progress']
        ).first()
        
        if not job:
            return Response({
                'error': 'No active generation job found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Mark job as canceled
        job.status = 'canceled'
        job.completed_at = timezone.now()
        job.save()
        
        serializer = ContentGenerationJobSerializer(job)
        return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_generated_content(request, project_id):
    """API endpoint to get generated content for a project"""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    contents = GeneratedContent.objects.filter(
        project=project
    ).order_by('order')
    
    serializer = GeneratedContentSerializer(contents, many=True)
    return Response(serializer.data)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_generated_content(request, content_id):
    """API endpoint to update a specific generated content"""
    content = get_object_or_404(GeneratedContent, id=content_id)
    
    # Ensure user has permission
    if content.project.user != request.user:
        return Response({
            'error': 'Permission denied'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Validate required fields
    if 'result' not in request.data:
        return Response({
            'error': 'Field "result" is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Update the content
    content.result = request.data['result']
    content.save()
    
    serializer = GeneratedContentSerializer(content)
    return Response(serializer.data)
