# projects/urls.py
from django.urls import path
from . import views
from . import ajax_views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('create/', views.project_create, name='project_create'),
    path('<uuid:project_id>/', views.project_detail, name='project_detail'),
    path('<uuid:project_id>/update/', views.project_update, name='project_update'),
    path('<uuid:project_id>/delete/', views.project_delete, name='project_delete'),
    
    # AJAX endpoints
    path('api/prompt-update/', ajax_views.prompt_update, name='prompt_update'),
    path('api/<uuid:project_id>/prompt-create/', ajax_views.prompt_create, name='prompt_create'),
    path('api/<uuid:project_id>/prompt-delete/<uuid:prompt_id>/', ajax_views.prompt_delete, name='prompt_delete'),
    path('api/<uuid:project_id>/generate-content/', ajax_views.generate_content, name='generate_content'),
    path('api/content-update/<uuid:content_id>/', ajax_views.update_generated_content, name='update_generated_content'),
]
