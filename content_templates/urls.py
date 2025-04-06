# content_templates/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.template_list, name='template_list'),
    path('create/', views.template_create, name='template_create'),
    path('<uuid:template_id>/', views.template_detail, name='template_detail'),
    path('<uuid:template_id>/update/', views.template_update, name='template_update'),
    path('<uuid:template_id>/delete/', views.template_delete, name='template_delete'),
]
