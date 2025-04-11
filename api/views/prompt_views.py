from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from projects.models import Project, Prompt
from content_templates.models import Template, TemplatePrompt
from ..serializers import PromptSerializer, TemplateSerializer, TemplatePromptSerializer
from prompts.utils.token_helper import getPromptTokenCount

class PromptViewSet(viewsets.ModelViewSet):
    queryset = Prompt.objects.all()
    serializer_class = PromptSerializer
    permission_classes = [IsAuthenticated]

class TemplateViewSet(viewsets.ModelViewSet):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
    permission_classes = [IsAuthenticated]

class TemplatePromptViewSet(viewsets.ModelViewSet):
    queryset = TemplatePrompt.objects.all()
    serializer_class = TemplatePromptSerializer
    permission_classes = [IsAuthenticated]

@api_view(['GET', 'POST', 'DELETE', 'PATCH'])
@permission_classes([IsAuthenticated])
def project_prompts(request, project_id):
    """
    Handle operations on project prompts
    """
    try:
        project = get_object_or_404(Project, id=project_id, user=request.user)
        
        if request.method == 'GET':
            # Get all prompts for the project
            prompts = Prompt.objects.filter(project=project).order_by('order')
            serializer = PromptSerializer(prompts, many=True)
            return Response(serializer.data)
            
        elif request.method == 'POST':
            # Create a new prompt
            data = request.data.copy()
            data['project'] = project.id
            
            # Set defaults if not provided
            data.setdefault('name', 'New Prompt')
            data.setdefault('prompt', '')
            data.setdefault('token_count', 0)
            
            # Get highest order and add 1
            highest_order = Prompt.objects.filter(project=project).order_by('-order').values_list('order', flat=True).first()
            data.setdefault('order', 0 if highest_order is None else highest_order + 1)
            
            serializer = PromptSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        elif request.method == 'DELETE':
            # Delete a prompt
            prompt_id = request.GET.get('promptId')
            if not prompt_id:
                return Response({"error": "promptId is required"}, status=status.HTTP_400_BAD_REQUEST)
                
            prompt = get_object_or_404(Prompt, id=prompt_id, project=project)
            prompt.delete()
            
            # Reorder remaining prompts
            remaining_prompts = Prompt.objects.filter(project=project).order_by('order')
            for i, p in enumerate(remaining_prompts):
                p.order = i
                p.save()
                
            return Response({"message": "Prompt deleted successfully"})
            
        elif request.method == 'PATCH':
            # Update a prompt
            data = request.data.copy()
            prompt_id = data.get('id')
            if not prompt_id:
                return Response({"error": "Prompt ID is required"}, status=status.HTTP_400_BAD_REQUEST)
                
            prompt = get_object_or_404(Prompt, id=prompt_id, project=project)
            
            # Calculate token count if prompt text is provided
            if 'prompt' in data:
                data['token_count'] = getPromptTokenCount(data['prompt'])
                
            serializer = PromptSerializer(prompt, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_template(request, project_id):
    """
    Import prompts from a template to a project
    """
    try:
        project = get_object_or_404(Project, id=project_id, user=request.user)
        
        template_id = request.data.get('templateId')
        if not template_id:
            return Response({"error": "Template ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        template = get_object_or_404(Template, id=template_id, user=request.user)
        
        # Fetch template prompts
        template_prompts = TemplatePrompt.objects.filter(template=template).order_by('order')
        
        # Get existing project prompts count for ordering
        existing_prompts = Prompt.objects.filter(project=project)
        start_order = existing_prompts.count()
        
        # Create new prompts from template prompts
        new_prompts = []
        for i, tp in enumerate(template_prompts):
            prompt = Prompt.objects.create(
                project=project,
                name=tp.name,
                prompt=tp.prompt,
                token_count=tp.token_count,
                order=start_order + i
            )
            new_prompts.append(prompt)
            
        serializer = PromptSerializer(new_prompts, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)