from django.db import models
from django.urls import reverse
from django.utils.text import slugify
import uuid

class DocumentationCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name_plural = "documentation categories"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("docs:category", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class DocumentationPage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(DocumentationCategory, on_delete=models.PROTECT, related_name='pages')
    content = models.TextField()
    order = models.IntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["category__order", "order", "title"]

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse("docs:page", kwargs={"category_slug": self.category.slug, "slug": self.slug})
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)