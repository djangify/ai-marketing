# content_templates/urls.py
from django.urls import path
from . import views
from . import ajax_views

app_name = 'content_templates'

urlpatterns = [
    path('', views.template_list, name='template_list'),
    path('create/', views.template_create, name='template_create'),
    path('<uuid:template_id>/', views.template_detail, name='template_detail'),
    path('<uuid:template_id>/update/', views.template_update, name='template_update'),
    path('<uuid:template_id>/delete/', views.template_delete, name='template_delete'),
    
    # New form-based prompt paths
    path('<uuid:template_id>/prompt/add/', views.template_prompt_add, name='template_prompt_add'),
    path('<uuid:template_id>/prompt/<uuid:prompt_id>/edit/', views.template_prompt_edit_page, name='template_prompt_edit_page'),
    path('<uuid:template_id>/prompt/<uuid:prompt_id>/delete/', views.template_prompt_delete_page, name='template_prompt_delete_page'),
    
    # Keep the prompt list endpoint for now
    path('api/<uuid:template_id>/prompt-edit/', views.template_prompt_edit, name='template_prompt_edit'),
    path('api/<uuid:template_id>/prompts/', views.template_prompt_list, name='template_prompt_list'),
    
    # AJAX endpoints to be deprecated
    #These can be commented out once the form-based approach is working
    # path('api/prompt-update/', ajax_views.template_prompt_update, name='template_prompt_update'),
    # path('api/<uuid:template_id>/prompt-create/', ajax_views.template_prompt_create, name='template_prompt_create'),
    # path('api/<uuid:template_id>/prompt-delete/<uuid:prompt_id>/', ajax_views.template_prompt_delete, name='template_prompt_delete'),
]