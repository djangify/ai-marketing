# content_templates/views.py
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Template, TemplatePrompt
from .forms import TemplateForm, TemplatePromptForm


@login_required
def template_list(request):
    # Start with all user's templates
    templates_query = request.user.templates.all()
    
    # Filter by tag if provided
    tag_filter = request.GET.get('tag')
    if tag_filter:
        from django.contrib.contenttypes.models import ContentType
        from core.models import Tag, TaggedItem
        
        # Get the tag by name
        try:
            tag = Tag.objects.get(name=tag_filter, user=request.user)
            
            # Get the content type for Template model
            template_content_type = ContentType.objects.get_for_model(Template)
            
            # Get template IDs that have this tag
            tagged_template_ids = TaggedItem.objects.filter(
                tag=tag,
                content_type=template_content_type
            ).values_list('object_id', flat=True)
            
            # Filter templates by these IDs
            templates_query = templates_query.filter(id__in=tagged_template_ids)
        except Tag.DoesNotExist:
            # If tag doesn't exist, just continue with all templates
            pass
    
    # Apply ordering
    templates = templates_query.order_by('-updated_at')
    
    # Annotate with prompt counts
    from django.db.models import Count
    templates = templates.annotate(prompt_count=Count('template_prompts'))
    
    # Pass the current tag filter to the template for UI feedback
    context = {
        'templates': templates,
        'current_tag': tag_filter
    }
    
    return render(request, 'content_templates/template_list.html', context)


@login_required
def template_create(request):
    if request.method == 'POST':
        form = TemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.user = request.user
            template.save()
            
            # Process tags if provided
            tags_string = form.cleaned_data.get('tags')
            if tags_string:
                # Get or create Tag objects and link them to the template
                from django.contrib.contenttypes.models import ContentType
                from core.models import Tag, TaggedItem
                
                template_content_type = ContentType.objects.get_for_model(Template)
                tag_names = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
                
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(
                        name=tag_name,
                        user=request.user
                    )
                    TaggedItem.objects.get_or_create(
                        tag=tag,
                        content_type=template_content_type,
                        object_id=template.id
                    )
            
            messages.success(request, "Template created successfully!")
            return redirect('content_templates:template_detail', template_id=template.id)
    else:
        form = TemplateForm()
    
    return render(request, 'content_templates/template_form.html', {'form': form, 'action': 'Create'})


@login_required
def template_detail(request, template_id):
    template = get_object_or_404(Template, id=template_id, user=request.user)
    
    # Get template prompts - this is the critical fix
    prompts = template.template_prompts.all().order_by('order')
    
    # Get associated tags
    from django.contrib.contenttypes.models import ContentType
    from core.models import TaggedItem
    
    template_content_type = ContentType.objects.get_for_model(Template)
    tagged_items = TaggedItem.objects.filter(
        content_type=template_content_type,
        object_id=template.id
    ).select_related('tag')
    
    tags = [item.tag.name for item in tagged_items]
    
    context = {
        'template': template,
        'prompts': prompts,  # Add prompts to the context
        'tags': tags,
    }
    
    return render(request, 'content_templates/template_detail.html', context)


@login_required
def template_update(request, template_id):
    template = get_object_or_404(Template, id=template_id, user=request.user)
    
    # Get existing tags for the template
    from django.contrib.contenttypes.models import ContentType
    from core.models import TaggedItem
    
    template_content_type = ContentType.objects.get_for_model(Template)
    tagged_items = TaggedItem.objects.filter(
        content_type=template_content_type,
        object_id=template.id
    ).select_related('tag')
    
    existing_tags = [item.tag.name for item in tagged_items]
    initial_data = {'tags': ', '.join(existing_tags)}
    
    if request.method == 'POST':
        form = TemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            
            # Process tags
            tags_string = form.cleaned_data.get('tags')
            if tags_string:
                # First remove existing tags
                TaggedItem.objects.filter(
                    content_type=template_content_type,
                    object_id=template.id
                ).delete()
                
                # Then add new tags
                from core.models import Tag
                
                tag_names = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
                
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(
                        name=tag_name,
                        user=request.user
                    )
                    TaggedItem.objects.get_or_create(
                        tag=tag,
                        content_type=template_content_type,
                        object_id=template.id
                    )
            
            messages.success(request, "Template updated successfully!")
            return redirect('content_templates:template_detail', template_id=template.id)
    else:
        form = TemplateForm(instance=template, initial=initial_data)
    
    return render(request, 'content_templates/template_form.html', {'form': form, 'template': template, 'action': 'Update'})

@login_required
def template_delete(request, template_id):
    template = get_object_or_404(Template, id=template_id, user=request.user)
    
    if request.method == 'POST':
        template.delete()
        messages.success(request, "Template deleted successfully!")
        return redirect('content_templates:template_list')
    
    return render(request, 'content_templates/template_confirm_delete.html', {'template': template})


@login_required
def template_prompt_list(request, template_id):
    template = get_object_or_404(Template, id=template_id, user=request.user)
    
    # Handle DELETE requests
    if request.method == 'DELETE':
        prompt_id = request.GET.get('id')
        if not prompt_id:
            return JsonResponse({'status': 'error', 'message': 'Prompt ID is required'}, status=400)
        
        try:
            prompt = get_object_or_404(TemplatePrompt, id=prompt_id, template=template)
            prompt.delete()
            
            # Reorder remaining prompts
            remaining_prompts = TemplatePrompt.objects.filter(template=template).order_by('order')
            for i, p in enumerate(remaining_prompts):
                p.order = i
                p.save()
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    # Normal GET request to display prompts
    prompts = template.prompts.all().order_by('order')
    return render(request, 'content_templates/template_prompt_list.html', {'prompts': prompts})


@login_required
def template_prompt_edit(request, template_id):
    template = get_object_or_404(Template, id=template_id, user=request.user)
    prompt_id = request.GET.get('prompt_id')
    prompt = get_object_or_404(TemplatePrompt, id=prompt_id, template=template)
    return render(request, 'content_templates/template_prompt_edit.html', {'prompt': prompt, 'template': template})


@login_required
def template_prompt_add(request, template_id):
    """Display and handle the template prompt creation page."""
    template = get_object_or_404(Template, id=template_id, user=request.user)
    
    if request.method == 'POST':
        # Handle form submission
        name = request.POST.get('name', 'New Prompt')
        prompt_text = request.POST.get('prompt', '')
        
        # Get the highest order value
        highest_order = TemplatePrompt.objects.filter(template=template).order_by('-order').values_list('order', flat=True).first() or -1
        next_order = highest_order + 1
        
        # Calculate token count
        from prompts.utils.token_helper import getPromptTokenCount
        token_count = getPromptTokenCount(prompt_text)
        
        # Create a new prompt
        template_prompt = TemplatePrompt.objects.create(
            template=template,
            name=name,
            prompt=prompt_text,
            order=next_order,
            token_count=token_count
        )
        
        messages.success(request, "Template prompt created successfully!")
        return redirect('content_templates:template_detail', template_id=template.id)
    
    # Display the form
    return render(request, 'content_templates/template_prompt_form.html', {'template': template})


@login_required
def template_prompt_edit_page(request, template_id, prompt_id):
    """Display and handle the template prompt editing page."""
    template = get_object_or_404(Template, id=template_id, user=request.user)
    template_prompt = get_object_or_404(TemplatePrompt, id=prompt_id, template=template)
    
    if request.method == 'POST':
        # Handle form submission
        name = request.POST.get('name', template_prompt.name)
        prompt_text = request.POST.get('prompt', template_prompt.prompt)
        
        # Calculate token count
        from prompts.utils.token_helper import getPromptTokenCount
        token_count = getPromptTokenCount(prompt_text)
        
        # Update the prompt
        template_prompt.name = name
        template_prompt.prompt = prompt_text
        template_prompt.token_count = token_count
        template_prompt.save()
        
        messages.success(request, "Template prompt updated successfully!")
        return redirect('content_templates:template_detail', template_id=template.id)
    
    # Display the form
    return render(request, 'content_templates/template_prompt_form.html', {'template': template, 'template_prompt': template_prompt})


@login_required
def template_prompt_delete_page(request, template_id, prompt_id):
    """Delete a template prompt."""
    template = get_object_or_404(Template, id=template_id, user=request.user)
    try:
        template_prompt = get_object_or_404(TemplatePrompt, id=prompt_id, template=template)
        
        if request.method == 'POST':
            # Delete the prompt
            template_prompt.delete()
            
            # Reorder remaining prompts
            remaining_prompts = TemplatePrompt.objects.filter(template=template).order_by('order')
            for i, p in enumerate(remaining_prompts):
                p.order = i
                p.save()
            
            messages.success(request, "Template prompt deleted successfully!")
            return redirect('content_templates:template_detail', template_id=template.id)
        
        # Display the confirmation page
        return render(request, 'content_templates/template_prompt_confirm_delete.html', {'template_prompt': template_prompt, 'template': template})
    except Exception as e:
        messages.error(request, f"Error deleting template prompt: {str(e)}")
        return redirect('content_templates:template_detail', template_id=template.id)