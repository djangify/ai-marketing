# prompts/urls.py
from django.urls import path
from . import views

app_name = 'prompts'

urlpatterns = [
    path('<uuid:project_id>/list/', views.prompt_list, name='prompt_list'),
    path('<uuid:project_id>/edit/', views.prompt_edit, name='prompt_edit'),
    path('<uuid:project_id>/create/', views.prompt_create, name='prompt_create'),
    path('<uuid:project_id>/delete/<uuid:prompt_id>/', views.prompt_delete, name='prompt_delete'),
    path('update/', views.prompt_update, name='prompt_update'),
    path('<uuid:project_id>/template-selection/', views.template_selection, name='template_selection'),
    path('<uuid:project_id>/import-template/', views.import_template, name='import_template'),
]
