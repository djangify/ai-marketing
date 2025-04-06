# content_templates/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Template, TemplatePrompt
from .forms import TemplateForm, TemplatePromptForm

@login_required
def template_list(request):
    templates = request.user.templates.all().order_by('-updated_at')
    return render(request, 'content_templates/template_list.html', {'templates': templates})

@login_required
def template_create(request):
    if request.method == 'POST':
        form = TemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.user = request.user
            template.save()
            messages.success(request, "Template created successfully!")
            return redirect('template_detail', template_id=template.id)
    else:
        form = TemplateForm()
    
    return render(request, 'content_templates/template_form.html', {'form': form, 'action': 'Create'})

@login_required
def template_detail(request, template_id):
    template = get_object_or_404(Template, id=template_id, user=request.user)
    prompts = template.prompts.all().order_by('order')
    
    prompt_id = request.GET.get('promptId')
    if prompt_id:
        selected_prompt = get_object_or_404(TemplatePrompt, id=prompt_id, template=template)
        context = {
            'template': template,
            'prompts': prompts,
            'selected_prompt': selected_prompt
        }
    else:
        context = {
            'template': template,
            'prompts': prompts
        }
    
    return render(request, 'content_templates/template_detail.html', context)

@login_required
def template_update(request, template_id):
    template = get_object_or_404(Template, id=template_id, user=request.user)
    
    if request.method == 'POST':
        form = TemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, "Template updated successfully!")
            return redirect('template_detail', template_id=template.id)
    else:
        form = TemplateForm(instance=template)
    
    return render(request, 'content_templates/template_form.html', {'form': form, 'template': template, 'action': 'Update'})

@login_required
def template_delete(request, template_id):
    template = get_object_or_404(Template, id=template_id, user=request.user)
    
    if request.method == 'POST':
        template.delete()
        messages.success(request, "Template deleted successfully!")
        return redirect('template_list')
    
    return render(request, 'content_templates/template_confirm_delete.html', {'template': template})
