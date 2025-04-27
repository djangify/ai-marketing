from django.urls import path
from . import views
from assets.views import asset_upload

app_name = 'assets'

urlpatterns = [
    path('project/<uuid:project_id>/assets/', views.asset_list, name='asset_list'),
    path('project/<uuid:project_id>/assets/upload/', views.asset_upload, name='asset_upload'),
    path('project/<uuid:project_id>/assets/<uuid:asset_id>/delete/', views.asset_delete, name='asset_delete'),
    path('project/<uuid:project_id>/assets/<uuid:asset_id>/', views.asset_detail, name='asset_detail'),
    path('project/<uuid:project_id>/asset-jobs/', views.asset_processing_jobs, name='asset_processing_jobs'),
    path('assets/', views.all_assets, name='all_assets'),
]
