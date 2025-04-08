# ai_marketing/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('projects/', include('projects.urls', namespace='projects')),
    path('prompts/', include('prompts.urls', namespace='prompts')),
    path('templates/', include('content_templates.urls', namespace='content_templates')),
    path('', include('core.urls', namespace='core')),
    path('subscriptions/', include('subscriptions.urls', namespace='subscriptions')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    