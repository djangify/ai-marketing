# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def index(request): 
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    return render(request, 'index.html')

def pricing(request):
    return render(request, 'core/pricing.html')