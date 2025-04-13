# prompts/urls.py
from django.urls import path
from . import views

app_name = 'prompts'

urlpatterns = [
    path('<uuid:project_id>/prompt/add/', views.prompt_add_page, name='prompt_add_page'),
    path('<uuid:project_id>/prompt/<uuid:prompt_id>/edit/', views.prompt_edit_page, name='prompt_edit_page'),
    path('<uuid:project_id>/list/', views.prompt_list, name='prompt_list'),
    path('<uuid:project_id>/delete/<uuid:prompt_id>/', views.prompt_delete, name='prompt_delete'),
    path('<uuid:project_id>/template-selection/', views.template_selection, name='template_selection'),
    path('<uuid:project_id>/import-template/', views.import_template, name='import_template'),
    
]
