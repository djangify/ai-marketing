# prompts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Prompt
from .forms import PromptForm
from content_templates.models import Template, TemplatePrompt
from projects.models import Project
import json


@login_required
def prompt_create(request, project_id):
    """Create a new prompt for the project."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
    
    try:
        project = get_object_or_404(Project, id=project_id, user=request.user)
        
        # Get the highest order value
        highest_order = Prompt.objects.filter(project=project).order_by('-order').values_list('order', flat=True).first() or -1
        next_order = highest_order + 1
        
        # Create a new prompt
        prompt = Prompt.objects.create(
            project=project,
            name="New Prompt",
            prompt="",
            order=next_order,
            token_count=0
        )
        
        # Return the new prompt as JSON
        return JsonResponse({
            'id': str(prompt.id),
            'name': prompt.name,
            'prompt': prompt.prompt,
            'order': prompt.order,
            'token_count': prompt.token_count
        })
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def prompt_update(request):
    """Update an existing prompt."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
    
    try:
        data = json.loads(request.body)
        prompt_id = data.get('id')
        name = data.get('name')
        prompt_text = data.get('prompt')
        
        prompt = get_object_or_404(Prompt, id=prompt_id)
        
        # Check if the prompt belongs to a project owned by the user
        if prompt.project.user != request.user:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        
        # Calculate token count
        from utils.token_helper import getPromptTokenCount
        token_count = getPromptTokenCount(prompt_text)
        
        # Update the prompt
        prompt.name = name
        prompt.prompt = prompt_text
        prompt.token_count = token_count
        prompt.save()
        
        # Return the updated prompt as JSON
        return JsonResponse({
            'id': str(prompt.id),
            'name': prompt.name,
            'prompt': prompt.prompt,
            'order': prompt.order,
            'token_count': prompt.token_count
        })
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def prompt_delete(request, project_id, prompt_id):
    """Delete a prompt."""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    prompt = get_object_or_404(Prompt, id=prompt_id, project=project)
    
    if request.method == 'DELETE':
        try:
            # Delete the prompt
            prompt.delete()
            
            # Reorder remaining prompts
            remaining_prompts = Prompt.objects.filter(project=project).order_by('order')
            for i, p in enumerate(remaining_prompts):
                p.order = i
                p.save()
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    # Handle GET request as appropriate for your app
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
    

@login_required
def prompt_list(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    prompts = project.project_prompts.all().order_by('order')
    return render(request, 'prompts/prompt_list.html', {'prompts': prompts, 'project': project})

@login_required
def prompt_edit(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    prompt_id = request.GET.get('prompt_id')
    prompt = get_object_or_404(Prompt, id=prompt_id, project=project)
    return render(request, 'prompts/prompt_edit.html', {'prompt': prompt, 'project': project})

@login_required
def template_selection(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    templates = Template.objects.filter(user=request.user)
    return render(request, 'prompts/template_selection.html', {'templates': templates, 'project': project})

@login_required
def import_template(request, project_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
    
    try:
        data = json.loads(request.body)
        template_id = data.get('templateId')
        if not template_id:
            return JsonResponse({'status': 'error', 'message': 'Template ID is required'}, status=400)
        
        project = get_object_or_404(Project, id=project_id, user=request.user)
        template = get_object_or_404(Template, id=template_id, user=request.user)
        
        # Fetch template prompts
        template_prompts = TemplatePrompt.objects.filter(template=template).order_by('order')
        
        # Fetch all existing project prompts
        existing_prompts = Prompt.objects.filter(project=project)
        
        # Calculate the starting order
        start_order = existing_prompts.count()
        
        # Create new prompts from template prompts
        new_prompts = []
        for i, tp in enumerate(template_prompts):
            prompt = Prompt.objects.create(
                project=project,
                name=tp.name,
                prompt=tp.prompt,
                order=start_order + i,
                token_count=tp.token_count
            )
            new_prompts.append(prompt)
        
        # Return the newly created prompts as JSON
        return JsonResponse([{
            'id': str(p.id),
            'name': p.name,
            'prompt': p.prompt,
            'order': p.order,
            'token_count': p.token_count
        } for p in new_prompts], safe=False)
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

