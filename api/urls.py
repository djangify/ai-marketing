from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import asset_views, content_views, prompt_views, subscription_views, content_generation_views

router = DefaultRouter()
router.register(r'assets', asset_views.AssetViewSet)
router.register(r'asset-processing-job', asset_views.AssetProcessingJobViewSet)
router.register(r'prompts', prompt_views.PromptViewSet)
router.register(r'generated-content', content_views.GeneratedContentViewSet)
router.register(r'templates', prompt_views.TemplateViewSet)
router.register(r'template-prompts', prompt_views.TemplatePromptViewSet)
router.register(r'generation-jobs', content_generation_views.ContentGenerationJobViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Asset processing endpoints
    path('asset/', asset_views.asset_detail, name='asset_detail'),
    path('asset-processing-job/', asset_views.asset_processing_job_list, name='asset_processing_job_list'),
    path('asset-processing-job/<uuid:project_id>/', asset_views.asset_processing_job_project, name='asset_processing_job_project'),
    
    
    # Content generation endpoints
    path('projects/<uuid:project_id>/generation/', content_generation_views.project_generation, name='project_generation'),
    path('projects/<uuid:project_id>/generated-content/', content_generation_views.project_generated_content, name='project_generated_content'),
    path('generated-content/<uuid:content_id>/', content_generation_views.update_generated_content, name='update_generated_content'),
    
    
    # Prompt endpoints
    path('projects/<uuid:project_id>/prompts/', prompt_views.project_prompts, name='project_prompts'),
    path('projects/<uuid:project_id>/import-template/', prompt_views.import_template, name='import_template'),
    path('projects/<uuid:project_id>/assets/', asset_views.asset_delete, name='asset_delete'),
    # Upload endpoint
    path('upload/', asset_views.upload, name='upload'),
    
    # Subscription endpoints
    path('create-checkout-session/', subscription_views.create_checkout_session, name='create_checkout_session'),
    path('create-portal-session/', subscription_views.create_portal_session, name='create_portal_session'),
    path('webhooks/stripe/', subscription_views.stripe_webhook, name='stripe_webhook'),
]
