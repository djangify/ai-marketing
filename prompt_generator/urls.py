# prompt_generator/urls.py
from django.urls import path
from . import views

app_name = 'prompt_generator'

urlpatterns = [
    path('generator/', views.prompt_generator_home, name='generator'),
    path('categories/', views.generator_categories, name='generator_categories'),  
    path('category/<uuid:category_id>/', views.generator_category, name='generator_category'),
    path('generate/<uuid:template_id>/', views.generate_prompt, name='generate_prompt'),
    path('save/', views.save_prompt, name='save_prompt'),
    path('templates/', views.generator_templates, name='generator_templates'), 
    path('prompt/<uuid:prompt_id>/', views.generator_detail, name='prompt_detail'),
    path('use-in-project/<uuid:prompt_id>/', views.use_in_project, name='use_in_project'),
    path('delete/<uuid:prompt_id>/', views.generator_confirm_delete, name='delete_prompt'),
]