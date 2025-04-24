from django.urls import path
from . import views

app_name = 'content_generation'

urlpatterns = [
    # Django views for template rendering
    path('<uuid:project_id>/status/', views.generation_status, name='generation_status'),
    path('<uuid:project_id>/generate/', views.generate_content, name='generate_content'),
    path('<uuid:content_id>/update/', views.update_generated_content, name='update_content'),
    path('<uuid:content_id>/download/', views.download_content, name='download_content'),
    path('<uuid:project_id>/download-batch/', views.download_batch, name='download_batch'),
    
    # AJAX endpoints
    path('api/<uuid:project_id>/start/', views.start_generation, name='start_generation'),
    path('api/<uuid:project_id>/status/', views.get_generation_status, name='get_status'),
    path('api/<uuid:project_id>/cancel/', views.cancel_generation, name='cancel_generation'),
    path('api/<uuid:content_id>/edit/', views.edit_generated_content, name='edit_content'),
]