from django.urls import path
from . import views

app_name = 'seo_optimization'

urlpatterns = [
    # Main URL patterns
    path('analyze/<uuid:content_id>/', views.analyze_content, name='analyze_content'),
    path('analysis/<uuid:analysis_id>/', views.analysis_detail, name='analysis_detail'),
    path('project/<uuid:project_id>/analyses/', views.project_analyses, name='project_analyses'),
    path('keywords/', views.keyword_tracking, name='keyword_tracking'),
    
    # AJAX endpoints
    path('api/analyze/', views.ajax_analyze_content, name='ajax_analyze_content'),
    path('api/meta-description/update/', views.ajax_update_meta_description, name='ajax_update_meta_description'),
    path('api/keyword/toggle-primary/', views.ajax_toggle_primary_keyword, name='ajax_toggle_primary_keyword'),
]