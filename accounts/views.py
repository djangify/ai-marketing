# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignUpForm, LoginForm, ProfileUpdateForm
from django.conf import settings
from prompts.models import Prompt
from assets.models import Asset
from prompts.utils.token_helper import formatTokens


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully! Welcome to AI Marketing Platform.")
            return redirect('accounts:dashboard')
    else:
        form = SignUpForm()
    
    return render(request, 'accounts/signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
        
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'accounts:dashboard')
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('accounts:login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated!")
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user.profile)
    
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def dashboard_view(request):
    # Get user projects
    projects = request.user.projects.all().order_by('-updated_at')
    
    # Calculate prompt token usage
    prompts = Prompt.objects.filter(project__user=request.user)
    
    prompt_token_count = sum(prompt.token_count or 0 for prompt in prompts)
    
    max_prompt_tokens = getattr(settings, 'MAX_TOKENS_PROMPTS', 20000)  # Default to 20,000 if not set
    prompt_token_percentage = min(round((prompt_token_count / max_prompt_tokens) * 100), 100)
    
    # Calculate asset token usage
    assets = Asset.objects.filter(project__user=request.user)
    asset_token_count = sum(asset.token_count or 0 for asset in assets)
    max_asset_tokens = getattr(settings, 'MAX_TOKENS_ASSETS', 100000)  # Default to 100,000 if not set
    asset_token_percentage = min(round((asset_token_count / max_asset_tokens) * 100), 100)
    
    # Format token counts for display
    formatted_prompt_tokens = formatTokens(prompt_token_count)
    formatted_asset_tokens = formatTokens(asset_token_count)
    
    # Prepare context
    context = {
        'projects': projects,
        'prompt_data': {
            'token_count': prompt_token_count,
            'formatted_token_count': formatted_prompt_tokens,
            'max_tokens': max_prompt_tokens,
            'percentage': prompt_token_percentage,
            'prompts_count': prompts.count(),
        },
        'asset_data': {
            'token_count': asset_token_count,
            'formatted_token_count': formatted_asset_tokens,
            'max_tokens': max_asset_tokens,
            'percentage': asset_token_percentage,
            'assets_count': assets.count(),
        }
    }
    
    return render(request, 'accounts/dashboard.html', context)

