# prompts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Prompt
from django.urls import reverse
from content_templates.models import Template, TemplatePrompt
from projects.models import Project
import json

@login_required
def prompt_add_page(request, project_id):
    """Display and handle the prompt creation page."""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    if request.method == 'POST':
        # Handle form submission
        name = request.POST.get('name', 'New Prompt')
        prompt_text = request.POST.get('prompt', '')
        
        # Get the highest order value
        highest_order = Prompt.objects.filter(project=project).order_by('-order').values_list('order', flat=True).first() or -1
        next_order = highest_order + 1
        
        # Calculate token count
        from prompts.utils.token_helper import getPromptTokenCount
        token_count = getPromptTokenCount(prompt_text)
        
        # Create a new prompt
        prompt = Prompt.objects.create(
            project=project,
            name=name,
            prompt=prompt_text,
            order=next_order,
            token_count=token_count
        )
        
        messages.success(request, "Prompt created successfully!")
        return redirect(reverse('projects:project_detail', kwargs={'project_id': project.id}) + '?tab=prompts')
    
    # Display the form
    return render(request, 'prompts/prompt_create.html', {'project': project})  

@login_required
def prompt_edit_page(request, project_id, prompt_id):
    """Display and handle the prompt editing page."""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    prompt = get_object_or_404(Prompt, id=prompt_id, project=project)
    
    if request.method == 'POST':
        # Handle form submission
        name = request.POST.get('name', prompt.name)
        prompt_text = request.POST.get('prompt', prompt.prompt)
        
        # Calculate token count
        from utils.token_helper import getPromptTokenCount
        token_count = getPromptTokenCount(prompt_text)
        
        # Update the prompt
        prompt.name = name
        prompt.prompt = prompt_text
        prompt.token_count = token_count
        prompt.save()
        
        messages.success(request, "Prompt updated successfully!")
        return redirect('projects:project_detail', project_id=project.id, tab='prompts')
    
    # Display the form
    return render(request, 'prompts/prompt_create.html', {'project': project, 'prompt': prompt})  # prompt_create.html is used for both create and edit

@login_required
def prompt_delete(request, project_id, prompt_id):
    """Delete a prompt."""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    try:
        prompt = get_object_or_404(Prompt, id=prompt_id, project=project)
        
        if request.method == 'POST':
            # Delete the prompt
            prompt.delete()
            
            # Reorder remaining prompts
            remaining_prompts = Prompt.objects.filter(project=project).order_by('order')
            for i, p in enumerate(remaining_prompts):
                p.order = i
                p.save()
            
            messages.success(request, "Prompt deleted successfully!")
            base_url = reverse('projects:project_detail', kwargs={'project_id': project.id})
            return redirect(f"{base_url}?tab=prompts")
        
        # Display the confirmation page
        return render(request, 'prompts/prompt_confirm_delete.html', {'prompt': prompt, 'project': project})
    except Exception as e:
        messages.error(request, f"Error deleting prompt: {str(e)}")
        base_url = reverse('projects:project_detail', kwargs={'project_id': project.id})
        return redirect(f"{base_url}?tab=prompts")
    

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
    
    # Check for error or message parameters
    error = request.GET.get('error')
    if error:
        messages.error(request, error)
    
    message = request.GET.get('message')
    if message:
        messages.success(request, message)
    
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
        
        # Check if this template is already imported
        template_prompt_names = [tp.name for tp in template_prompts]
        existing_prompts = Prompt.objects.filter(project=project, name__in=template_prompt_names)
        
        if existing_prompts.exists():
            return JsonResponse({
                'status': 'error', 
                'message': f'This template appears to be already imported into this project',
            }, status=400)
        
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
        
        # Store success message in session
        request.session['import_success'] = f"Successfully imported {len(new_prompts)} prompts from template: {template.title}"
        
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
    