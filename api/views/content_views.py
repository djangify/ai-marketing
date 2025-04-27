# content_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from projects.models import Project, GeneratedContent, Asset, Prompt
from ..serializers import GeneratedContentSerializer
import openai
from django.conf import settings

class GeneratedContentViewSet(viewsets.ModelViewSet):
    queryset = GeneratedContent.objects.all()
    serializer_class = GeneratedContentSerializer
    permission_classes = [IsAuthenticated]

@api_view(['GET', 'POST', 'DELETE', 'PATCH'])
@permission_classes([IsAuthenticated])
def project_generated_content(request, project_id):
    """
    Handle operations on project generated content
    """
    try:
        project = get_object_or_404(Project, id=project_id, user=request.user)

        if request.method == 'GET':
            # Get all generated content for the project
            generated_content = GeneratedContent.objects.filter(project=project).order_by('order')
            serializer = GeneratedContentSerializer(generated_content, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            # Fetch assets and prompts
            assets = Asset.objects.filter(project=project)
            prompts_qs = Prompt.objects.filter(project=project).order_by('order')

            if not assets.filter(content__isnull=False).exists():
                return Response(
                    {"error": "Project has no assets with content"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not prompts_qs.exists():
                return Response(
                    {"error": "Project has no prompts"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Determine which prompts to generate for
            prompt_ids = request.data.get('prompt_ids', [])
            if prompt_ids:
                # regenerate only the chosen prompts
                to_generate = prompts_qs.filter(id__in=prompt_ids)
                names = to_generate.values_list('name', flat=True)
                GeneratedContent.objects.filter(
                    project=project,
                    name__in=names
                ).delete()
            else:
                # append-only: skip prompts that already have content
                existing = GeneratedContent.objects.filter(project=project) \
                                  .values_list('name', flat=True)
                to_generate = prompts_qs.exclude(name__in=existing)

            if not to_generate.exists():
                return Response(
                    {"error": "No prompts to generate content for"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Prepare the asset summary
            content_from_assets = "\n\n".join(
                asset.content for asset in assets if asset.content
            )

            # Initialize OpenAI client
            client = openai.Client(api_key=settings.OPENAI_API_KEY)
            models = ["gpt-4o", "gpt-3.5-turbo"]
            created = []

            # Generate content for each missing/regenerated prompt
            for prompt in to_generate:
                text = None
                for model in models:
                    try:
                        resp = client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": "You are a content generation assistant"},
                                {"role": "user", "content": f"""
Use the following prompt and summary to generate new content:
** PROMPT:
{prompt.prompt}
---------------------
** SUMMARY:
{content_from_assets}
"""}
                            ]
                        )
                        text = resp.choices[0].message.content
                        break
                    except Exception as e:
                        # retry on rate limits or overloads
                        if getattr(e, 'status_code', None) in [429, 503] or 'overloaded' in str(e):
                            continue
                        else:
                            raise

                if not text:
                    return Response(
                        {"error": f"Failed to generate content for prompt '{prompt.name}'"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                obj = GeneratedContent.objects.create(
                    project=project,
                    name=prompt.name,
                    result=text,
                    order=prompt.order
                )
                created.append(obj)

            # Return the full up-to-date list
            all_content = GeneratedContent.objects.filter(project=project).order_by('order')
            serializer = GeneratedContentSerializer(all_content, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            # Delete all generated content for the project
            GeneratedContent.objects.filter(project=project).delete()
            return Response({"message": "Generated content deleted"}, status=status.HTTP_200_OK)

        elif request.method == 'PATCH':
            # Update a specific generated content
            content_id = request.data.get('id')
            result = request.data.get('result')
            if not content_id or result is None:
                return Response(
                    {"error": "ID and result are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            content = get_object_or_404(GeneratedContent, id=content_id, project=project)
            content.result = result
            content.save()
            serializer = GeneratedContentSerializer(content)
            return Response(serializer.data)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
