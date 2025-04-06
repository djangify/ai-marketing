# content_templates/ajax_views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
import json
from .models import Template, TemplatePrompt

@login_required
@require_POST
def template_prompt_update(request):
    try:
        data = json.loads(request.body)
        prompt_id = data.get('prompt_id')
        name = data.get('name')
        prompt_text = data.get('prompt')
        
        prompt = get_object_or_404(TemplatePrompt, id=prompt_id)
        
        # Check if the prompt belongs to a template owned by the user
        if prompt.template.user != request.user:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        
        prompt.name = name
        prompt.prompt = prompt_text
        prompt.save()
        
        return JsonResponse({
            'status': 'success',
            'prompt': {
                'id': prompt.id,
                'name': prompt.name,
                'prompt': prompt.prompt,
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def template_prompt_create(request, template_id):
    try:
        template = get_object_or_404(Template, id=template_id, user=request.user)
        
        # Get the highest order value
        highest_order = TemplatePrompt.objects.filter(template=template).order_by('-order').values_list('order', flat=True).first() or -1
        next_order = highest_order + 1
        
        prompt = TemplatePrompt.objects.create(
            template=template,
            name="New Prompt",
            prompt="",
            order=next_order
        )
        
        return JsonResponse({
            'status': 'success',
            'prompt': {
                'id': prompt.id,
                'name': prompt.name,
                'prompt': prompt.prompt,
                'order': prompt.order,
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def template_prompt_delete(request, template_id, prompt_id):
    try:
        template = get_object_or_404(Template, id=template_id, user=request.user)
        prompt = get_object_or_404(TemplatePrompt, id=prompt_id, template=template)
        
        prompt.delete()
        
        # Re-order remaining prompts
        remaining_prompts = TemplatePrompt.objects.filter(template=template).order_by('order')
        for i, p in enumerate(remaining_prompts):
            p.order = i
            p.save()
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    