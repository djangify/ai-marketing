import openai
import time
import logging
from django.conf import settings
from django.utils import timezone
from .models import ContentGenerationJob, AIConfig
from projects.models import Project, GeneratedContent

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        # Get active AI config or use default values
        try:
            self.config = AIConfig.objects.filter(is_active=True).first()
        except Exception as e:
            logger.warning(f"Failed to load AI config: {e}")
            self.config = None
    
    def generate_content(self, prompt_text, content_source, max_retries=2):
        """
        Generate content using OpenAI API with retry and fallback mechanisms
        
        Args:
            prompt_text (str): The prompt to send to OpenAI
            content_source (str): Source content to use for generation
            max_retries (int): Maximum number of retries before failing
            
        Returns:
            str: Generated content text
        """
        # Get model configuration
        primary_model = self.config.model_name if self.config else "gpt-4o"
        fallback_model = self.config.fallback_model if self.config else "gpt-4o-mini"
        temperature = self.config.temperature if self.config else 0.7
        
        models_to_try = [primary_model, fallback_model]
        
        for attempt in range(max_retries + 1):
            for model in models_to_try:
                try:
                    response = self.openai_client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are a content generation assistant."},
                            {"role": "user", "content": f"""
                            Use the following prompt and summary to generate new content:
                            ** PROMPT:
                            {prompt_text}
                            ---------------------
                            ** SUMMARY:
                            {content_source}
                            """}
                        ],
                        temperature=temperature,
                    )
                    
                    return response.choices[0].message.content
                
                except openai.RateLimitError:
                    # If it's a rate limit error, wait and retry
                    if attempt < max_retries:
                        # Exponential backoff
                        wait_time = (2 ** attempt) + 1
                        logger.warning(f"Rate limit reached with model {model}. Waiting {wait_time}s before retry.")
                        time.sleep(wait_time)
                    else:
                        # Try the fallback model if we haven't already
                        continue
                
                except Exception as e:
                    # For any other error, log it and try the fallback model
                    logger.error(f"Error using {model}: {str(e)}")
                    # If we're on the last model, raise the error
                    if model == models_to_try[-1]:
                        raise
        
        # If we get here, all retries and fallbacks failed
        raise Exception("Failed to generate content after all retries and fallbacks")


class GenerationManager:
    """Manager for handling the content generation process"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    def start_generation_job(self, project_id, user):
        """Start a content generation job for a project"""
        try:
            project = Project.objects.get(id=project_id)
            
            # Clean up any existing content
            GeneratedContent.objects.filter(project=project).delete()
            
            # Check if assets have content
            assets_with_content = project.client_assets.filter(content__isnull=False).exclude(content='')
            if not assets_with_content.exists():
                raise ValueError("No assets with content found in this project")
            
            # Check if prompts exist
            prompts = project.project_prompts.all().order_by('order')
            if not prompts.exists():
                raise ValueError("No prompts found in this project")
            
            # Create new generation job
            job = ContentGenerationJob.objects.create(
                project=project,
                user=user,
                status='in_progress',
                prompts_total=prompts.count(),
                prompts_completed=0
            )
            
            return job
        except Exception as e:
            print(f"Error creating generation job: {str(e)}")
            return None
        
    def process_generation_job(self, job_id):
        """Process a generation job"""
        try:
            job = ContentGenerationJob.objects.get(id=job_id)
            if not job:
                print(f"Job with ID {job_id} not found")
                return
            
            project = job.project
            print(f"Processing generation job {job_id} for project {project.id}")
            
            # Get assets content
            print("Getting asset content...")
            assets = project.client_assets.filter(content__isnull=False).exclude(content='')
            print(f"Found {assets.count()} assets with content")
            
            if assets.count() > 0:
                print("Asset IDs with content:", list(assets.values_list('id', flat=True)))
            
            content_from_assets = "\n\n".join([asset.content for asset in assets if asset.content])
            print(f"Total characters from asset content: {len(content_from_assets)}")
            
            # If content is too long, truncate it to a reasonable size
            max_content_length = 24000  # Approximately 6000 tokens
            if len(content_from_assets) > max_content_length:
                content_from_assets = content_from_assets[:max_content_length] + "\n[Content truncated due to length...]"
            
            # Get prompts
            prompts = project.project_prompts.all().order_by('order')
            
            # Get active AI config or use default
            try:
                ai_config = AIConfig.objects.filter(is_active=True).first()
                if not ai_config:
                    ai_config = AIConfig.objects.create(
                        name="Default Config",
                        model_name=settings.OPENAI_DEFAULT_MODEL,
                        fallback_model=settings.OPENAI_FALLBACK_MODEL,
                        temperature=0.7,
                        max_tokens=4000,
                        is_active=True
                    )
            except Exception as e:
                print(f"Error getting AI config: {e}")
                ai_config = None
            
            # Set up OpenAI client
            openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Generate content for each prompt
            for i, prompt in enumerate(prompts):
                try:
                    # Configure model settings
                    model = ai_config.model_name if ai_config else settings.OPENAI_DEFAULT_MODEL
                    temperature = ai_config.temperature if ai_config else 0.7
                    max_tokens = ai_config.max_tokens if ai_config else 4000
                    
                    # Make API call to OpenAI
                    response = openai_client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are a content generation assistant."},
                            {"role": "user", "content": f"""
                            Use the following prompt and summary to generate new content:
                            
                            ** PROMPT:
                            {prompt.prompt}
                            
                            ** SOURCE CONTENT:
                            {content_from_assets}
                            """}
                        ],
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    # Extract generated text
                    generated_text = response.choices[0].message.content.strip()
                    
                    # Save generated content
                    GeneratedContent.objects.create(
                        project=project,
                        name=prompt.name,
                        result=generated_text,
                        order=i
                    )
                    
                    # Update job progress
                    job.prompts_completed += 1
                    job.save(update_fields=['prompts_completed'])  
                    # Use update_fields for more frequent updates
                    print(f"Progress update: {job.prompts_completed} of {job.prompts_total} ({int((job.prompts_completed/job.prompts_total)*100)}%)")
                    
                    # Small delay to prevent rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error generating content for prompt {prompt.id}: {e}")
                    # Continue to next prompt on error
            
            # Mark job as completed
            job.status = 'completed'
            job.completed_at = timezone.now()
            job.save()

            # Add a success message
            from django.contrib import messages
            try:
                # Add message to the request context or session if available
                from django.contrib.messages import constants as message_constants
                from django.contrib.messages.storage.fallback import FallbackStorage
                
                print(f"Content generation completed successfully! Generated {job.prompts_completed} items.")
            except Exception as e:
                print(f"Could not add success message: {e}")
                        
        except Exception as e:
            # Mark job as failed
            if job:
                job.status = 'failed'
                job.error_message = str(e)
                job.completed_at = timezone.now()
                job.save()
            print(f"Error processing generation job {job_id}: {e}")
            raise