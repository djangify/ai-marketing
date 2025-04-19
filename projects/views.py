# projects/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Project
from .forms import ProjectForm
from .models import Project


@login_required
def project_list(request):
    # Start with all user's projects
    projects_query = request.user.projects.all()
    
    # Filter by tag if provided
    tag_filter = request.GET.get('tag')
    if tag_filter:
        from django.contrib.contenttypes.models import ContentType
        from core.models import Tag, TaggedItem
        
        # Get the tag by name
        try:
            tag = Tag.objects.get(name=tag_filter, user=request.user)
            
            # Get the content type for Project model
            project_content_type = ContentType.objects.get_for_model(Project)
            
            # Get project IDs that have this tag
            tagged_project_ids = TaggedItem.objects.filter(
                tag=tag,
                content_type=project_content_type
            ).values_list('object_id', flat=True)
            
            # Filter projects by these IDs
            projects_query = projects_query.filter(id__in=tagged_project_ids)
        except Tag.DoesNotExist:
            # If tag doesn't exist, just continue with all projects
            pass
    
    # Apply ordering
    projects = projects_query.order_by('-updated_at')
    
    # Pass the current tag filter to the template for UI feedback
    context = {
        'projects': projects,
        'current_tag': tag_filter
    }
    
    return render(request, 'projects/project_list.html', context)


def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()
            
            # Process tags if provided
            tags_string = form.cleaned_data.get('tags')
            if tags_string:
                # Get or create Tag objects and link them to the project
                from django.contrib.contenttypes.models import ContentType
                from core.models import Tag, TaggedItem
                
                project_content_type = ContentType.objects.get_for_model(Project)
                tag_names = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
                
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(
                        name=tag_name,
                        user=request.user
                    )
                    TaggedItem.objects.get_or_create(
                        tag=tag,
                        content_type=project_content_type,
                        object_id=project.id
                    )
            
            messages.success(request, "Project created successfully!")
            return redirect('projects:project_detail', project_id=project.id)
    else:
        form = ProjectForm()
    
    return render(request, 'projects/project_form.html', {'form': form, 'action': 'Create'})

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    # Get associated tags
    from django.contrib.contenttypes.models import ContentType
    from core.models import TaggedItem
    
    project_content_type = ContentType.objects.get_for_model(Project)
    tagged_items = TaggedItem.objects.filter(
        content_type=project_content_type,
        object_id=project.id
    ).select_related('tag')
    
    tags = [item.tag.name for item in tagged_items]
    
    # Check for success message from template import
    if 'import_success' in request.session:
        messages.success(request, request.session['import_success'])
        del request.session['import_success']  # Clear the message from session
        
    tab = request.GET.get('tab', 'upload')
    
    context = {
        'project': project,
        'tab': tab,
        'tags': tags,  
    }
    
    if tab == 'upload':
        assets = project.assets.all().order_by('-updated_at')
        context['assets'] = assets
    elif tab == 'prompts':
        prompts = project.project_prompts.all().order_by('order')
        context['prompts'] = prompts
    elif tab == 'generate':
        generated_contents = project.generated_contents.all().order_by('order')
        context['generated_contents'] = generated_contents
    
    return render(request, 'projects/project_detail.html', context)


@login_required
def project_update(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "Project updated successfully!")
            return redirect('projects:project_detail', project_id=project.id)
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'projects/project_form.html', {'form': form, 'project': project, 'action': 'Update'})

@login_required
def project_delete(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    if request.method == 'POST':
        project.delete()
        messages.success(request, "Project deleted successfully!")
        return redirect('projects:project_list')
    
    return render(request, 'projects/project_confirm_delete.html', {'project': project})
