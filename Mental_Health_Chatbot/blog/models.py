# blog/models.py

from django.db import models
# blog/models.py

# from django.db import models

class Blog(models.Model):
    title = models.CharField(max_length=255)
    summary = models.TextField()
    link = models.URLField()
    views = models.IntegerField(default=0)
    category = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)  # <--- Add this line
    # image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    # image_url = models.URLField(blank=True, null=True) 
    image_name = models.CharField(max_length=100, blank=True)  # like 'mental_health.jpg'


    def __str__(self):
        return self.title
