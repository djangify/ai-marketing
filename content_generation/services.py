# services.py
import openai
import time
import logging
from django.conf import settings
from django.utils import timezone
from .models import ContentGenerationJob, AIConfig
from projects.models import Project, GeneratedContent, Prompt
from .prompt_enhancement import PromptEnhancer

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for interacting with OpenAI API"""
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        try:
            self.config = AIConfig.objects.filter(is_active=True).first()
        except Exception as e:
            logger.warning(f"Failed to load AI config: {e}")
            self.config = None

    def generate_content(self, prompt_text, content_source, content_type="general", max_retries=2):
        primary = self.config.model_name if self.config else "gpt-4o"
        fallback = self.config.fallback_model if self.config else "gpt-3.5-turbo"
        temp = self.config.temperature if self.config else 0.7

        messages = PromptEnhancer.enhance_prompt(
            user_prompt=prompt_text,
            content_type=content_type,
            asset_content=content_source
        )
        for attempt in range(max_retries + 1):
            for model in (primary, fallback):
                try:
                    resp = self.openai_client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temp
                    )
                    return resp.choices[0].message.content
                except openai.RateLimitError:
                    if attempt < max_retries:
                        wait = (2 ** attempt) + 1
                        logger.warning(f"Rate limit on {model}, retrying in {wait}s")
                        time.sleep(wait)
                        continue
                except Exception as e:
                    logger.error(f"Error with {model}: {e}")
                    if model == fallback:
                        raise
        raise Exception("All retries/fallbacks failed")

class GenerationManager:
    """Manager for handling the content generation process"""

    def __init__(self):
        self.openai_service = OpenAIService()

    def start_generation_job(self, project_id, user, prompt_ids=None):
        project = Project.objects.get(id=project_id)

        # Selectively delete or skip
        if prompt_ids:
            to_generate = project.project_prompts.filter(id__in=prompt_ids).order_by('order')
            names = to_generate.values_list('name', flat=True)
            GeneratedContent.objects.filter(project=project, name__in=names).delete()
        else:
            existing = GeneratedContent.objects.filter(project=project) \
                              .values_list('name', flat=True)
            to_generate = project.project_prompts.exclude(name__in=existing) \
                               .order_by('order')

        if not to_generate.exists():
            raise ValueError("No new prompts to generate for this project")

        # Ensure there is asset content
        assets = project.client_assets.filter(content__isnull=False).exclude(content='')
        if not assets.exists():
            raise ValueError("No assets with content found in this project")

        # Create the job for exactly these prompts
        job = ContentGenerationJob.objects.create(
            project=project,
            user=user,
            status='in_progress',
            prompts_total=to_generate.count(),
            prompts_completed=0
        )
        return job

    def process_generation_job(self, job_id):
        job = ContentGenerationJob.objects.get(id=job_id)
        project = job.project

        # Gather and truncate asset content
        assets = project.client_assets.filter(content__isnull=False).exclude(content='')
        content_src = "\n\n".join(a.content for a in assets)
        if len(content_src) > 24000:
            content_src = content_src[:24000] + "\n[Content truncated]"

        # Only generate for prompts without existing content
        existing = GeneratedContent.objects.filter(project=project) \
                          .values_list('name', flat=True)
        prompts = project.project_prompts.exclude(name__in=existing).order_by('order')

        # Get or build AIConfig
        ai_conf = AIConfig.objects.filter(is_active=True).first()
        if not ai_conf:
            ai_conf = AIConfig.objects.create(
                name="Default Config",
                model_name=settings.OPENAI_DEFAULT_MODEL,
                fallback_model=settings.OPENAI_FALLBACK_MODEL,
                temperature=0.7,
                max_tokens=4000,
                is_active=True
            )

        # Generate for each prompt
        for idx, prompt in enumerate(prompts):
            try:
                ctype = PromptEnhancer.detect_content_type(prompt.prompt)
                text = self.openai_service.generate_content(
                    prompt_text=prompt.prompt,
                    content_source=content_src,
                    content_type=ctype
                )
                GeneratedContent.objects.create(
                    project=project,
                    name=prompt.name,
                    result=text,
                    order=idx
                )
                job.prompts_completed += 1
                job.save(update_fields=['prompts_completed'])
                time.sleep(1)
            except Exception as e:
                logger.error(f"Failed on prompt {prompt.id}: {e}")
                continue

        job.status = 'completed'
        job.completed_at = timezone.now()
        job.save()
        logger.info(f"Generation job {job_id} completed ({job.prompts_completed}/{job.prompts_total})")
