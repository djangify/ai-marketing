# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing/home.html')

def pricing(request):
    return render(request, 'landing/pricing.html')