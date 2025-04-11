# api/utils.py
import os
import uuid
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.utils import timezone

class CPanelFileStorage:
    """
    File storage service for cPanel hosting
    """
    def __init__(self):
        self.storage = FileSystemStorage()
        self.media_root = settings.MEDIA_ROOT
        
    def generate_filename(self, project_id, original_filename):
        """Generate a unique filename with project ID as prefix"""
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        filename, extension = os.path.splitext(original_filename)
        return f"{project_id}/{timestamp}_{unique_id}{extension}"
        
    def save_file(self, file_obj, project_id):
        """Save the file to storage and return the file URL"""
        filename = self.generate_filename(project_id, file_obj.name)
        
        # Create directory if it doesn't exist
        project_dir = os.path.join(self.media_root, str(project_id))
        os.makedirs(project_dir, exist_ok=True)
        
        # Save the file
        saved_path = self.storage.save(filename, file_obj)
        file_url = self.storage.url(saved_path)
        
        return {
            'filename': filename,
            'url': file_url,
            'size': file_obj.size
        }
        
    def delete_file(self, file_path):
        """Delete a file from storage"""
        if self.storage.exists(file_path):
            self.storage.delete(file_path)
            return True
        return False
    