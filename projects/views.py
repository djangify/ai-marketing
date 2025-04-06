# projects/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Project, Asset, AssetProcessingJob, Prompt, GeneratedContent
from .forms import ProjectForm, PromptForm

@login_required
def project_list(request):
    projects = request.user.projects.all().order_by('-updated_at')
    return render(request, 'projects/project_list.html', {'projects': projects})

@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()
            messages.success(request, "Project created successfully!")
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm()
    
    return render(request, 'projects/project_form.html', {'form': form, 'action': 'Create'})

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    tab = request.GET.get('tab', 'upload')
    
    context = {
        'project': project,
        'tab': tab,
    }
    
    if tab == 'upload':
        assets = project.assets.all().order_by('-updated_at')
        context['assets'] = assets
    elif tab == 'prompts':
        prompts = project.prompts.all().order_by('order')
        prompt_id = request.GET.get('promptId')
        if prompt_id:
            selected_prompt = get_object_or_404(Prompt, id=prompt_id, project=project)
            context['selected_prompt'] = selected_prompt
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
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'projects/project_form.html', {'form': form, 'project': project, 'action': 'Update'})

@login_required
def project_delete(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    if request.method == 'POST':
        project.delete()
        messages.success(request, "Project deleted successfully!")
        return redirect('project_list')
    
    return render(request, 'projects/project_confirm_delete.html', {'project': project})
