import os
import re
from .models import AssetProcessingJob
import tiktoken

def create_asset_processing_job(asset, project):
    """Create a processing job for an asset"""
    job = AssetProcessingJob.objects.create(
        asset=asset,
        project=project,
        status='created',
        attempts=0,
    )
    return job

def get_token_count(text):
    """
    Estimate token count based on whitespace-delimited words
    This is a simple approximation; for production, use a proper tokenizer like tiktoken
    """
    encoding = tiktoken.get_encoding("cl100k_base")  # Use the appropriate encoding
    tokens = encoding.encode(text)
    return len(tokens)

def process_text_file(file_path):
    """Process a text file and return content and token count"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    token_count = get_token_count(content)
    return content, token_count

def extract_file_extension(filename):
    """Extract file extension from filename"""
    _, ext = os.path.splitext(filename)
    return ext.lower()