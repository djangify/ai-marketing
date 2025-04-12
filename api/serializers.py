from rest_framework import serializers
from projects.models import Project, Asset, AssetProcessingJob, Prompt, GeneratedContent
from content_templates.models import Template, TemplatePrompt
from subscriptions.models import Subscription
from content_generation.models import ContentGenerationJob, AIConfig

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = '__all__'

class AssetProcessingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetProcessingJob
        fields = '__all__'

class PromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prompt
        fields = '__all__'

class GeneratedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedContent
        fields = '__all__'

class GeneratedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedContent
        fields = '__all__'

class ContentGenerationJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentGenerationJob
        fields = '__all__'

class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = '__all__'

class TemplatePromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplatePrompt
        fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'

class ContentGenerationJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentGenerationJob
        fields = '__all__'

class AIConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIConfig
        fields = '__all__'