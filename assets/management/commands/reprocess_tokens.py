# assets/management/commands/reprocess_tokens.py
from django.core.management.base import BaseCommand
from django.conf import settings
import os
from assets.models import Asset
from assets.utils import determine_process_function, get_token_count
import time

class Command(BaseCommand):
    help = 'Reprocesses all assets to correct token counts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project',
            type=str,
            help='Only reprocess assets for a specific project ID',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of assets to process in each batch',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        project_id = options.get('project')
        batch_size = options.get('batch_size')
        dry_run = options.get('dry_run')
        
        if project_id:
            self.stdout.write(f"Processing assets for project {project_id}")
            assets = Asset.objects.filter(project_id=project_id)
        else:
            self.stdout.write(f"Processing all assets")
            assets = Asset.objects.all()
        
        total_assets = assets.count()
        self.stdout.write(f"Found {total_assets} assets to process")
        
        processed = 0
        updated = 0
        errors = 0
        
        # Process in batches to avoid memory issues with large datasets
        offset = 0
        
        while offset < total_assets:
            batch = assets[offset:offset+batch_size]
            self.stdout.write(f"Processing batch {offset//batch_size + 1} ({len(batch)} assets)")
            
            for asset in batch:
                try:
                    self.stdout.write(f"Processing asset: {asset.title} (ID: {asset.id})")
                    
                    file_path = os.path.join(settings.MEDIA_ROOT, asset.file_name)
                    
                    # Check if file exists
                    if not os.path.exists(file_path):
                        self.stdout.write(self.style.WARNING(
                            f"File not found for asset {asset.id}: {file_path}"
                        ))
                        errors += 1
                        continue
                    
                    # Process based on file type
                    process_func = determine_process_function(asset.file_type, asset.mime_type)
                    original_token_count = asset.token_count
                    
                    # Get content and token count
                    content, token_count = process_func(file_path)
                    
                    # If no tokens were counted, try to estimate from file size
                    if token_count == 0 and asset.size > 0:
                        token_count = max(1, int(asset.size / 4))  # Rough estimate
                        self.stdout.write(self.style.WARNING(
                            f"Zero tokens counted, using size-based estimate: {token_count}"
                        ))
                    
                    if original_token_count != token_count:
                        self.stdout.write(
                            f"  Token count change: {original_token_count} → {token_count}"
                        )
                        
                        if not dry_run:
                            asset.token_count = token_count
                            asset.save(update_fields=['token_count'])
                        updated += 1
                    else:
                        self.stdout.write(
                            f"  Token count unchanged: {token_count}"
                        )
                    
                    processed += 1
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"Error processing asset {asset.id}: {str(e)}"
                    ))
                    errors += 1
            
            # Update offset for next batch
            offset += batch_size
            
            # Small delay between batches to prevent overloading the system
            time.sleep(0.1)
        
        self.stdout.write(self.style.SUCCESS(
            f"Completed! Processed: {processed}, Updated: {updated}, Errors: {errors}"
        ))
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                "This was a dry run - no changes were made to the database."
            ))
            