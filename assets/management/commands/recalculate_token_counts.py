# assets/management/commands/recalculate_token_counts.py
from django.core.management.base import BaseCommand
from assets.models import Asset
from assets.utils import update_asset_token_count

class Command(BaseCommand):
    help = 'Recalculates token counts for all assets'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project',
            type=str,
            help='Only recalculate token counts for assets in the specified project ID',
        )

    def handle(self, *args, **options):
        project_id = options.get('project')
        
        if project_id:
            assets = Asset.objects.filter(project_id=project_id)
            self.stdout.write(f"Recalculating token counts for assets in project {project_id}...")
        else:
            assets = Asset.objects.all()
            self.stdout.write(f"Recalculating token counts for all {assets.count()} assets...")
        
        success_count = 0
        error_count = 0
        
        for asset in assets:
            try:
                result = update_asset_token_count(asset, force_recount=True)
                if result:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error recalculating tokens for asset {asset.id}: {e}"))
                error_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"Finished recalculating token counts for {success_count} assets."))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f"Encountered errors for {error_count} assets."))
            