import os
import re

from django.conf import settings
from .models import AssetProcessingJob
import tiktoken
import io

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
    Get an accurate token count using tiktoken.
    """
    if not text:
        return 0
    
    try:
        encoding = tiktoken.get_encoding("cl100k_base")  # Use the appropriate encoding
        tokens = encoding.encode(text)
        return len(tokens)
    except Exception as e:
        print(f"Error counting tokens: {e}")
        # Fallback to a simple word count estimation if tiktoken fails
        word_count = len(text.split())
        print(f"Falling back to word count estimation: {word_count} words")
        return word_count

def process_text_file(file_path):
    """Process a text file and return content and token count"""
    content = ""
    token_count = 0
    
    print(f"Processing text file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get token count before sanitization to ensure accurate counts
        token_count = get_token_count(content)
        print(f"Text file token count (before sanitizing): {token_count}")
        return content, token_count
    except UnicodeDecodeError as e:
        print(f"UTF-8 decode error: {e}, trying latin-1")
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            token_count = get_token_count(content)
            print(f"Text file token count (latin-1): {token_count}")
            return content, token_count
        except Exception as e:
            print(f"Latin-1 fallback error: {e}")
            return "", 0
    except Exception as e:
        print(f"Unexpected error processing text file: {e}")
        return "", 0

def process_pdf_file(file_path):
    """Process a PDF file and return extracted text and token count"""
    content = ""
    token_count = 0
    
    print(f"Processing PDF file: {file_path}")
    try:
        import PyPDF2
        text = ""
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page_num in range(len(pdf_reader.pages)):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    text += page_text if page_text else ""
                except Exception as page_e:
                    print(f"Error extracting page {page_num}: {page_e}")
                    continue
        
        # Get token count before sanitization
        token_count = get_token_count(text)
        print(f"PDF token count (before sanitizing): {token_count}")
        content = text
        return content, token_count
    except ImportError as e:
        print(f"PyPDF2 import error: {e}")
        return "", 0
    except Exception as e:
        print(f"Unexpected error processing PDF: {e}")
        return "", 0

def process_markdown_file(file_path):
    """Process a markdown file just like a text file but recognize it's markdown"""
    return process_text_file(file_path)

def determine_process_function(file_type, mime_type):
    """Determine which processing function to use based on file type and MIME type"""
    if file_type in ['text', 'markdown']:
        return process_text_file
    elif mime_type == 'application/pdf' or file_type == 'pdf':
        return process_pdf_file
    else:
        # Default to text file processing for unknown types
        return process_text_file

def extract_file_extension(filename):
    """Extract file extension from filename"""
    _, ext = os.path.splitext(filename)
    return ext.lower()

def update_asset_token_count(asset, force_recount=False):
    """Update the token count for an asset"""
    if not asset.content or force_recount:
        # Try to reprocess the file if we have access to it
        try:
            file_path = os.path.join(settings.MEDIA_ROOT, asset.file_name)
            process_func = determine_process_function(asset.file_type, asset.mime_type)
            content, token_count = process_func(file_path)
            
            # Update the asset with new content and token count
            asset.content = content
            asset.token_count = token_count
            asset.save()
            return True
        except Exception as e:
            print(f"Error updating asset token count: {e}")
            return False
    else:
        # Just recount tokens for the existing content
        asset.token_count = get_token_count(asset.content)
        asset.save()
        return True