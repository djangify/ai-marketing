# docs/urls.py
from django.urls import path
from . import views

app_name = 'docs'

urlpatterns = [
    path('', views.docs_home, name='documentation'),
    path('<slug:slug>/', views.category_detail, name='category'),
    path('<slug:category_slug>/<slug:slug>/', views.page_detail, name='page'),
]