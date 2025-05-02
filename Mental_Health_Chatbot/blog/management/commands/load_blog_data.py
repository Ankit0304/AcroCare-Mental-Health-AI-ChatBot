from django.core.management.base import BaseCommand
from blog.models import Blog

class Command(BaseCommand):
    help = 'Load initial blog content'

    def handle(self, *args, **kwargs):
        blog_data = [
            {
                "title": "Why Mental Health Is Important",
                "summary": "Learn why mental health is as important as physical health and what you can do to support it.",
                "link": "https://www.verywellmind.com/mental-health-importance-5197820",
                "image_url": "https://source.unsplash.com/featured/?mental-health"
            },
            {
                "title": "How to Practice Mindfulness Every Day",
                "summary": "Simple ways to integrate mindfulness into your daily routine for better peace and clarity.",
                "link": "https://www.headspace.com/mindfulness/mindfulness-for-everyday-life",
                "image_url": "https://source.unsplash.com/featured/?mindfulness"
            },
            {
                "title": "Coping Strategies for Anxiety",
                "summary": "Explore expert-backed strategies for managing anxiety in your daily life.",
                "link": "https://www.psychologytoday.com/us/blog/in-practice/202010/10-strategies-manage-anxiety",
                "image_url": "https://source.unsplash.com/featured/?anxiety"
            },
            {
                "title": "How Journaling Can Improve Your Mental Health",
                "summary": "Discover how putting your thoughts on paper can lead to improved emotional well-being.",
                "link": "https://positivepsychology.com/benefits-of-journaling/",
                "image_url": "https://source.unsplash.com/featured/?journaling"
            },
            {
                "title": "The Science of Gratitude and Mental Health",
                "summary": "Understand the connection between gratitude and improved mental well-being.",
                "link": "https://www.health.harvard.edu/healthbeat/giving-thanks-can-make-you-happier",
                "image_url": "https://source.unsplash.com/featured/?gratitude"
            },
            {
                "title": "Managing Stress in a Busy World",
                "summary": "Techniques to help you stay grounded and reduce stress despite your busy schedule.",
                "link": "https://www.helpguide.org/articles/stress/stress-management.htm",
                "image_url": "https://source.unsplash.com/featured/?stress-relief"
            },
            {
                "title": "The Link Between Sleep and Mental Health",
                "summary": "How quality sleep impacts your emotional resilience and mental wellness.",
                "link": "https://www.sleepfoundation.org/mental-health",
                "image_url": "https://source.unsplash.com/featured/?sleep,mental-health"
            },
            {
                "title": "How to Support a Friend Struggling With Mental Health",
                "summary": "Practical advice on how to be there for someone going through a hard time.",
                "link": "https://www.mhanational.org/tips-talking-and-supporting-someone-mental-health",
                "image_url": "https://source.unsplash.com/featured/?support,friends"
            }
        ]

        for entry in blog_data:
            blog, created = Blog.objects.get_or_create(
                title=entry['title'],
                defaults={
                    'summary': entry['summary'],
                    'link': entry['link'],
                    'image_url': entry['image_url'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Added blog: {entry['title']}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Skipped (already exists): {entry['title']}"))
