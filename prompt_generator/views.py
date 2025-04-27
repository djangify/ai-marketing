# prompt_generator/views.py
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from subscriptions.utils import subscription_required
from .models import GeneratorCategory, GeneratorTemplate, GeneratorParameter, GeneratedPrompt
from .forms import PromptGeneratorForm, SaveGeneratedPromptForm
from prompts.utils.token_helper import getPromptTokenCount
from prompts.utils.token_tracker import add_prompt_tokens
import json

@login_required
@subscription_required
def prompt_generator_home(request):
    """Home page for the prompt generator"""
    categories = GeneratorCategory.objects.filter(is_active=True)
    featured_templates = GeneratorTemplate.objects.filter(is_active=True, is_featured=True)
    recent_prompts = GeneratedPrompt.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'categories': categories,
        'featured_templates': featured_templates,
        'recent_prompts': recent_prompts,
    }
    
    return render(request, 'prompt_generator/generator.html', context)

@login_required
@subscription_required
def generator_categories(request):
    """View all generator categories"""
    categories = GeneratorCategory.objects.filter(is_active=True)
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'prompt_generator/generator_categories.html', context)

@login_required
@subscription_required
def generator_category(request, category_id):
    """View templates for a specific category"""
    category = get_object_or_404(GeneratorCategory, id=category_id, is_active=True)
    templates = GeneratorTemplate.objects.filter(category=category, is_active=True)
    
    context = {
        'category': category,
        'templates': templates,
    }
    
    return render(request, 'prompt_generator/generator_category.html', context)

@login_required
@subscription_required
def generate_prompt(request, template_id):
    """Generate a prompt using a template"""
    template = get_object_or_404(GeneratorTemplate, id=template_id, is_active=True)
    parameters = template.parameters.all().order_by('order')
    
    if request.method == 'POST':
        # Process submitted parameters
        param_values = {}
        for param in parameters:
            if param.parameter_type == 'checkbox':
                # Handle multiple checkbox values
                selected_values = []
                # Look for checkbox values with index suffixes
                for key in request.POST:
                    if key.startswith(f"{param.name}_"):
                        selected_values.append(request.POST.get(key))
                param_values[param.name] = ", ".join(selected_values) if selected_values else ""
            else:
                param_values[param.name] = request.POST.get(param.name, param.default_value)
        
        # Generate prompt by replacing parameters in template
        prompt_text = template.template_text
        for param_name, param_value in param_values.items():
            # Handle different template variable formats
            replacements = [
                f"{{{param_name}}}",           # {param_name}
                f"{{{{ {param_name} }}}}",     # {{ param_name }}
                f"{param_name}",               # param_name (without braces)
            ]
            for replacement in replacements:
                prompt_text = prompt_text.replace(replacement, param_value)
        
        # Calculate token count
        token_count = getPromptTokenCount(prompt_text)
        
        # Create form for saving the prompt
        save_form = SaveGeneratedPromptForm(initial={
            'name': f"{template.name} - {template.category.name}",
            'prompt_text': prompt_text
        })
        
        context = {
            'template': template,
            'parameters': parameters,
            'prompt_text': prompt_text,
            'token_count': token_count,
            'param_values': param_values,
            'save_form': save_form,
        }
        
        return render(request, 'prompt_generator/generator_result.html', context)
    
    # Create a dynamic form based on the template parameters
    form = PromptGeneratorForm(initial={'template': template})
    
    # Add fields for each parameter
    for param in parameters:
        field_kwargs = {
            'label': param.display_name,
            'help_text': param.description,
            'required': param.is_required,
            'initial': param.default_value,
            'widget': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main'})
        }
        
        if param.parameter_type == 'select':
            # Split by comma and strip whitespace from each option
            choices = [(opt.strip(), opt.strip()) for opt in param.options.split(',') if opt.strip()]
            field_kwargs['widget'] = forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main'})
            field_kwargs['choices'] = choices
            form.fields[param.name] = forms.ChoiceField(**field_kwargs)
        
        elif param.parameter_type == 'radio':
            # Split by comma and strip whitespace from each option
            choices = [(opt.strip(), opt.strip()) for opt in param.options.split(',') if opt.strip()]
            field_kwargs['widget'] = forms.RadioSelect(attrs={'class': 'mr-2'})
            field_kwargs['choices'] = choices
            form.fields[param.name] = forms.ChoiceField(**field_kwargs)
        
        elif param.parameter_type == 'checkbox':
            # Split by comma and strip whitespace from each option
            choices = [(opt.strip(), opt.strip()) for opt in param.options.split(',') if opt.strip()]
            field_kwargs['widget'] = forms.CheckboxSelectMultiple(attrs={'class': 'mr-2'})
            field_kwargs['choices'] = choices
            field_kwargs['required'] = False  # Make it non-required so user can select none
            form.fields[param.name] = forms.MultipleChoiceField(**field_kwargs)
        
        else:  # text input
            form.fields[param.name] = forms.CharField(**field_kwargs)
    
    context = {
        'template': template,
        'parameters': parameters,
        'form': form,
    }
    
    return render(request, 'prompt_generator/generator_prompt.html', context)

@login_required
@subscription_required
def save_prompt(request):
    """Save a generated prompt"""
    if request.method == 'POST':
        # Debug the incoming data
        print("POST data:", request.POST)
        
        # Ensure name and prompt_text are present
        name = request.POST.get('name')
        prompt_text = request.POST.get('prompt_text')
        
        if not name or not prompt_text:
            messages.error(request, "Name and prompt text are required.")
            return redirect('prompt_generator:generator')
            
        # Create the prompt object directly rather than using the form
        prompt = GeneratedPrompt(
            user=request.user,
            name=name,
            prompt_text=prompt_text
        )
        
        # Get template ID from hidden field if available
        template_id = request.POST.get('template_id')
        if template_id:
            try:
                template = GeneratorTemplate.objects.get(id=template_id)
                prompt.template = template
            except GeneratorTemplate.DoesNotExist:
                pass  # Continue without template association
        
        # Store parameters used
        param_values = {}
        for key, value in request.POST.items():
            if key.startswith('param_'):
                param_name = key[6:]  # Remove 'param_' prefix
                param_values[param_name] = value
        
        prompt.parameters_used = param_values
        
        # Calculate token count
        prompt.token_count = getPromptTokenCount(prompt.prompt_text)
        
        # Add to user's token usage
        add_prompt_tokens(request.user, prompt.token_count)
        
        prompt.save()
        
        messages.success(request, "Prompt saved successfully!")
        return redirect('prompt_generator:generator_templates.html')
    
    # For non-POST requests or if we get here due to errors
    messages.error(request, "Invalid request method for saving prompt.")
    return redirect('prompt_generator:generator')

@login_required
@subscription_required
def generator_templates(request):
    """View user's saved prompts"""
    prompts = GeneratedPrompt.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'prompts': prompts,
    }
    
    return render(request, 'prompt_generator/generator_templates.html', context)

@login_required
@subscription_required
def generator_detail(request, prompt_id):
    """View a specific prompt"""
    prompt = get_object_or_404(GeneratedPrompt, id=prompt_id, user=request.user)
    
    context = {
        'prompt': prompt,
    }
    
    return render(request, 'prompt_generator/generator_detail.html', context)

@login_required
@subscription_required
def use_in_project(request, prompt_id):
    """Use a generated prompt in a project"""
    if request.method == 'POST':
        prompt = get_object_or_404(GeneratedPrompt, id=prompt_id, user=request.user)
        project_id = request.POST.get('project_id')
        
        if not project_id:
            messages.error(request, "Please select a project")
            return redirect('prompt_generator:generator_prompt', prompt_id=prompt_id)
        
        # Create a new prompt in the selected project
        from projects.models import Project, Prompt
        
        project = get_object_or_404(Project, id=project_id, user=request.user)
        
        # Get highest order for new prompt
        highest_order = Prompt.objects.filter(project=project).order_by('-order').values_list('order', flat=True).first() or -1
        next_order = highest_order + 1
        
        # Create the prompt
        project_prompt = Prompt.objects.create(
            project=project,
            name=prompt.name,
            prompt=prompt.prompt_text,
            token_count=prompt.token_count,
            order=next_order
        )
        
        messages.success(request, f"Prompt added to project: {project.title}")
        return redirect('projects:project_detail', project_id=project.id, tab='prompts')
    
    return redirect('prompt_generator:generator_detail', prompt_id=prompt_id)

@login_required
def generator_confirm_delete(request, prompt_id):
    """Delete a generated prompt"""
    prompt = get_object_or_404(GeneratedPrompt, id=prompt_id, user=request.user)
    
    if request.method == 'POST':
        prompt.delete()
        messages.success(request, "Prompt deleted successfully")
        return redirect('prompt_generator:generator_templates')
    
    context = {
        'prompt': prompt,
    }
    
    return render(request, 'prompt_generator/generator_confirm_delete.html', context)