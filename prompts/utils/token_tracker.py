# prompts/utils/token_tracker.py
from accounts.models import TokenUsage
from django.utils import timezone

def ensure_token_usage_exists(user):
    """Ensure the user has a TokenUsage record"""
    token_usage, created = TokenUsage.objects.get_or_create(user=user)
    return token_usage

def add_prompt_tokens(user, token_count):
    """Add tokens to a user's usage counter"""
    token_usage = ensure_token_usage_exists(user)
    token_usage.prompt_tokens_used += token_count
    token_usage.save()
    return token_usage

def add_asset_tokens(user, token_count):
    """Add asset tokens to a user's usage counter"""
    token_usage = ensure_token_usage_exists(user)
    token_usage.asset_tokens_used += token_count
    token_usage.save()
    return token_usage

def update_prompt_tokens(user, old_token_count, new_token_count):
    """Update prompt tokens when editing a prompt"""
    token_usage = ensure_token_usage_exists(user)
    # If new count is higher, add the difference
    if new_token_count > old_token_count:
        token_usage.prompt_tokens_used += (new_token_count - old_token_count)
        token_usage.save()
    return token_usage

def get_prompt_tokens_used(user):
    """Get the number of prompt tokens used by a user"""
    token_usage = ensure_token_usage_exists(user)
    return token_usage.prompt_tokens_used

def get_asset_tokens_used(user):
    """Get the number of asset tokens used by a user"""
    token_usage = ensure_token_usage_exists(user)
    return token_usage.asset_tokens_used

def reset_token_usage(user):
    """Reset token usage for a user on subscription renewal"""
    token_usage = ensure_token_usage_exists(user)
    token_usage.reset_usage()
    return token_usage
