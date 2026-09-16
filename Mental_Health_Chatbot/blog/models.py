from django.db import models
from django.contrib.auth.models import User


class Blog(models.Model):
    title = models.CharField(max_length=255)
    summary = models.TextField()
    content = models.TextField(blank=True, help_text="Full article content if published directly on ACROCARE")
    link = models.URLField(max_length=500, blank=True, null=True, help_text="Original external article link if scraped")
    category = models.CharField(max_length=100, default='General')
    source = models.CharField(max_length=150, default='ACROCARE Editorial')
    read_time = models.CharField(max_length=50, default='3 min read')
    image_url = models.URLField(max_length=500, blank=True, null=True)
    image_name = models.CharField(max_length=100, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='blogs')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
