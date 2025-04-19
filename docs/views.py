# docs/views.py
from django.shortcuts import render, get_object_or_404
from .models import DocumentationCategory, DocumentationPage

def docs_home(request):
    """Display documentation homepage with categories"""
    categories = DocumentationCategory.objects.all()
    
    # Get the first page if it exists
    first_page = DocumentationPage.objects.filter(is_published=True).first()
    
    context = {
        'categories': categories,
        'first_page': first_page,
        'title': 'Documentation',
        'active_page': 'docs_home',
    }
    return render(request, 'docs/docs_home.html', context)

def category_detail(request, slug):
    """Display documentation category with pages"""
    category = get_object_or_404(DocumentationCategory, slug=slug)
    pages = category.pages.filter(is_published=True)
    
    # Get the first page in the category if it exists
    first_page = pages.first()
    
    context = {
        'category': category,
        'pages': pages,
        'first_page': first_page,
        'title': f'{category.name} - Documentation',
        'active_page': 'docs_category',
    }
    return render(request, 'docs/category_detail.html', context)

def page_detail(request, category_slug, slug):
    """Display a specific documentation page"""
    page = get_object_or_404(DocumentationPage, slug=slug, category__slug=category_slug, is_published=True)
    
    # Get all categories and pages for the sidebar
    categories = DocumentationCategory.objects.all()
    
    # Get next and previous pages within the same category
    try:
        next_page = DocumentationPage.objects.filter(
            category=page.category,
            order__gt=page.order,
            is_published=True
        ).order_by('order').first()
    except:
        next_page = None
    
    try:
        prev_page = DocumentationPage.objects.filter(
            category=page.category,
            order__lt=page.order,
            is_published=True
        ).order_by('-order').first()
    except:
        prev_page = None
    
    context = {
        'page': page,
        'categories': categories,
        'next_page': next_page,
        'prev_page': prev_page,
        'title': f'{page.title} - Documentation',
        'active_page': 'docs_page',
    }
    return render(request, 'docs/page_detail.html', context)
