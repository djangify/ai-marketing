# prompts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from .models import Prompt
from django.urls import reverse
from content_templates.models import Template, TemplatePrompt
from projects.models import Project
import json
from prompts.utils.token_tracker import add_prompt_tokens, update_prompt_tokens


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
        
        # Track token usage
        from prompts.utils.token_tracker import add_prompt_tokens
        add_prompt_tokens(request.user, token_count)
        
        messages.success(request, "Prompt created successfully!")
        return redirect(reverse('projects:project_detail', kwargs={'project_id': project.id}) + '?tab=prompts') 

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
        from prompts.utils.token_helper import getPromptTokenCount
        old_token_count = prompt.token_count
        new_token_count = getPromptTokenCount(prompt_text)
        
        # Update the token usage if token count increased
        if new_token_count > old_token_count:
            from prompts.utils.token_tracker import update_prompt_tokens
            update_prompt_tokens(request.user, old_token_count, new_token_count)
        
        prompt.name = name
        prompt.prompt = prompt_text
        prompt.token_count = new_token_count
        prompt.save()
        
        messages.success(request, "Prompt updated successfully!")
        return redirect('projects:project_detail', project_id=project.id, tab='prompts')
    
    # Display the form
    return render(request, 'prompts/prompt_create.html', {'project': project, 'prompt': prompt})


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
    
    # Check if this is an error page or a modal
    error = request.GET.get('error')
    
    # If error parameter exists, serve a full page rather than modal
    if error:
        context = {
            'templates': templates,
            'project': project,
            'error': error,
            'is_error_page': True
        }
        return render(request, 'prompts/template_selection_page.html', context)
        
    # Otherwise, serve the modal as normal
    context = {
        'templates': templates,
        'project': project
    }
    return render(request, 'prompts/template_selection.html', context)

@login_required
def import_template(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
    
    try:
        # Handle both AJAX JSON and form submissions
        if request.headers.get('Content-Type') == 'application/json':
            data = json.loads(request.body)
            template_id = data.get('templateId')
        else:
            template_id = request.POST.get('templateId')
            
        if not template_id:
            error_message = "Please select a template"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': error_message}, status=400)
            else:
                return redirect(reverse('prompts:template_selection', kwargs={'project_id': project.id}) + f"?error={error_message}")
        
        template = get_object_or_404(Template, id=template_id, user=request.user)
        
        # Fetch template prompts
        template_prompts = TemplatePrompt.objects.filter(template=template).order_by('order')
        
        # Check if this template is already imported
        template_prompt_names = [tp.name for tp in template_prompts]
        existing_prompts = Prompt.objects.filter(project=project, name__in=template_prompt_names)
        
        if existing_prompts.exists():
            error_message = "This template appears to be already imported into this project"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': error_message}, status=400)
            else:
                return redirect(reverse('prompts:template_selection', kwargs={'project_id': project.id}) + f"?error={error_message}")
        
        # Fetch all existing project prompts
        existing_prompts = Prompt.objects.filter(project=project)
        
        # Calculate the starting order
        start_order = existing_prompts.count()
        
        # Create new prompts from template prompts
        new_prompts = []
        total_new_tokens = 0
        for i, tp in enumerate(template_prompts):
            prompt = Prompt.objects.create(
                project=project,
                name=tp.name,
                prompt=tp.prompt,
                order=start_order + i,
                token_count=tp.token_count
            )
            total_new_tokens += tp.token_count
            new_prompts.append(prompt)

        # Track token usage for all imported prompts
        add_prompt_tokens(request.user, total_new_tokens)
        
        # Store success message in session
        request.session['import_success'] = f"Successfully imported {len(new_prompts)} prompts from template: {template.title}"
        
        # Return based on request type
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return the newly created prompts as JSON for AJAX
            return JsonResponse([{
                'id': str(p.id),
                'name': p.name,
                'prompt': p.prompt,
                'order': p.order,
                'token_count': p.token_count
            } for p in new_prompts], safe=False)
        else:
            # Redirect for form submission
            return redirect('projects:project_detail', project_id=project.id, tab='prompts')
        
    except Exception as e:
        error_message = str(e)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': error_message}, status=500)
        else:
            return redirect(reverse('prompts:template_selection', kwargs={'project_id': project.id}) + f"?error={error_message}")
