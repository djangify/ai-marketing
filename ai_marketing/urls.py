# ai_marketing/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views.asset_views import AssetViewSet, AssetProcessingJobViewSet
from django.views.static import serve


router = DefaultRouter()
router.register(r'assets', AssetViewSet, basename='asset')
router.register(r'asset-processing-jobs', AssetProcessingJobViewSet, basename='asset-processing-job')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('', include('core.urls', namespace='core')),
    path('projects/', include('projects.urls', namespace='projects')),
    path('prompts/', include('prompts.urls', namespace='prompts')),
    path('templates/', include('content_templates.urls', namespace='content_templates')),
    path('blog/', include('blog.urls', namespace='blog')),
    path('content_generation/', include('content_generation.urls', namespace='content_generation')),
    path('documentation/', include('docs.urls', namespace='docs')),
    path('assets/', include('assets.urls', namespace='assets')),
    path('subscriptions/', include('subscriptions.urls', namespace='subscriptions')),
    path('seo/', include('seo_optimization.urls', namespace='seo_optimization')),
    path('api/', include(router.urls)),
    path('prompt-generator/', include('prompt_generator.urls', namespace='prompt_generator')),
    path('media/<path:path>', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]

    