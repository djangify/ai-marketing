from django.urls import path
from . import views
from assets.views import asset_upload

app_name = 'assets'

urlpatterns = [
    path('<uuid:project_id>/assets/', views.asset_list, name='asset_list'),
    path('<uuid:project_id>/assets/upload/', views.asset_upload, name='asset_upload'),
    path('<uuid:project_id>/assets/delete/', views.asset_delete, name='asset_delete'),
    path('<uuid:project_id>/assets/<uuid:asset_id>/', views.asset_detail, name='asset_detail'),
    path('<uuid:project_id>/asset-processing-jobs/', views.asset_processing_jobs, name='asset_processing_jobs'),
]
