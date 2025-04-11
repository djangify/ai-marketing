from django.urls import path
from . import views
from assets.views import upload_file

app_name = 'assets'

urlpatterns = [
    path('<uuid:project_id>/list/', views.asset_list, name='asset_list'),
    path('<uuid:project_id>/upload/', views.asset_upload, name='asset_upload'),
    path('<uuid:project_id>/delete/', views.asset_delete, name='asset_delete'),
    path('<uuid:project_id>/asset/<uuid:asset_id>/', views.asset_detail, name='asset_detail'),
    path('api/upload/', upload_file, name='upload_file'),
]
