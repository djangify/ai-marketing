# projects/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('create/', views.project_create, name='project_create'),
    path('<uuid:project_id>/', views.project_detail, name='project_detail'),
    path('<uuid:project_id>/update/', views.project_update, name='project_update'),
    path('<uuid:project_id>/delete/', views.project_delete, name='project_delete'),
]
