# prompt_generator/urls.py
from django.urls import path
from . import views

app_name = 'prompt_generator'

urlpatterns = [
    # Generator home/dashboard
    path('generator/', views.prompt_generator_home, name='generator'),

    # All categories
    path('categories/', views.generator_categories, name='generator_categories'),

    # Templates in one category
    path('category/<uuid:category_id>/', views.generator_category, name='generator_category'),

    # Fill-in-the-blanks form & POST to generate
    path('generate/<uuid:template_id>/', views.generate_prompt, name='generate_prompt'),

    # Save a generated prompt
    path('save/', views.save_prompt, name='save_prompt'),

    # View your saved prompts
    path('templates/', views.generator_templates, name='generator_templates'),

    # Detail page for one saved prompt
    path('prompt/<uuid:prompt_id>/', views.generator_detail, name='prompt_detail'),

    # Use a saved prompt in a project
    path('use-in-project/<uuid:prompt_id>/', views.use_in_project, name='use_in_project'),

    # Confirm & delete a saved prompt
    path('delete/<uuid:prompt_id>/', views.generator_confirm_delete, name='delete_prompt'),
]
