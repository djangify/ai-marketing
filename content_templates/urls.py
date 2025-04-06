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
    
    # AJAX endpoints
    path('api/prompt-update/', ajax_views.template_prompt_update, name='template_prompt_update'),
    path('api/<uuid:template_id>/prompt-create/', ajax_views.template_prompt_create, name='template_prompt_create'),
    path('api/<uuid:template_id>/prompt-delete/<uuid:prompt_id>/', ajax_views.template_prompt_delete, name='template_prompt_delete'),
]