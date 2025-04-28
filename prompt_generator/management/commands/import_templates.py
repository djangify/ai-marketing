from django.core.management.base import BaseCommand
from prompt_generator.models import GeneratorCategory, GeneratorTemplate, GeneratorParameter
import json
import os
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import generator templates from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the JSON file')
        parser.add_argument('--clear', action='store_true', help='Clear existing data before import')

    def handle(self, *args, **options):
        file_path = options['file_path']
        clear_existing = options.get('clear', False)
        
        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f'File not found: {file_path}'))
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR(f'Invalid JSON in file: {file_path}'))
            return
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error reading file: {str(e)}'))
            return
        
        # Clear existing data if requested
        if clear_existing:
            self.stdout.write('Clearing existing generator data...')
            GeneratorParameter.objects.all().delete()
            GeneratorTemplate.objects.all().delete()
            GeneratorCategory.objects.all().delete()
        
        # Import categories
        self.import_categories(data.get('categories', []))
        
        # Import templates
        self.import_templates(data.get('templates', []))
        
        self.stdout.write(self.style.SUCCESS('Import completed successfully'))
    
    def import_categories(self, categories):
        """Import generator categories"""
        self.stdout.write('Importing categories...')
        categories_created = 0
        
        for category_data in categories:
            try:
                category, created = GeneratorCategory.objects.update_or_create(
                    name=category_data['name'],
                    defaults={
                        'description': category_data.get('description', ''),
                        'icon': category_data.get('icon', ''),
                        'is_active': category_data.get('is_active', True),
                        'order': category_data.get('order', 0)
                    }
                )
                
                if created:
                    categories_created += 1
                    self.stdout.write(f'  Created category: {category.name}')
                else:
                    self.stdout.write(f'  Updated category: {category.name}')
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'  Error importing category {category_data.get("name", "unknown")}: {str(e)}'))
        
        self.stdout.write(f'Categories imported: {categories_created}')
    
    def import_templates(self, templates):
        """Import generator templates and their parameters"""
        self.stdout.write('Importing templates...')
        templates_created = 0
        parameters_created = 0
        
        for template_data in templates:
            try:
                # Get the category
                category_name = template_data.get('category')
                if not category_name:
                    self.stderr.write(self.style.WARNING(f'  Skipping template {template_data.get("name", "unknown")}: No category specified'))
                    continue
                
                try:
                    category = GeneratorCategory.objects.get(name=category_name)
                except GeneratorCategory.DoesNotExist:
                    self.stderr.write(self.style.WARNING(f'  Skipping template {template_data.get("name", "unknown")}: Category {category_name} not found'))
                    continue
                
                # Create or update the template
                template, created = GeneratorTemplate.objects.update_or_create(
                    name=template_data['name'],
                    category=category,
                    defaults={
                        'description': template_data.get('description', ''),
                        'template_text': template_data.get('template_text', ''),
                        'is_featured': template_data.get('is_featured', False),
                        'is_active': template_data.get('is_active', True)
                    }
                )
                
                if created:
                    templates_created += 1
                    self.stdout.write(f'  Created template: {template.name}')
                else:
                    self.stdout.write(f'  Updated template: {template.name}')
                
                # Import parameters for this template
                parameters = template_data.get('parameters', [])
                for param_data in parameters:
                    param, param_created = GeneratorParameter.objects.update_or_create(
                        template=template,
                        name=param_data['name'],
                        defaults={
                            'display_name': param_data.get('display_name', param_data['name']),
                            'description': param_data.get('description', ''),
                            'parameter_type': param_data.get('parameter_type', 'text'),
                            'options': param_data.get('options', ''),
                            'default_value': param_data.get('default_value', ''),
                            'is_required': param_data.get('is_required', True),
                            'order': param_data.get('order', 0)
                        }
                    )
                    
                    if param_created:
                        parameters_created += 1
            
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'  Error importing template {template_data.get("name", "unknown")}: {str(e)}'))
        
        self.stdout.write(f'Templates imported: {templates_created}')
        self.stdout.write(f'Parameters imported: {parameters_created}')