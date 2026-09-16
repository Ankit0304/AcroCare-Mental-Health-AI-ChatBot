from django.core.management.base import BaseCommand
from blog.models import Blog
from blog.utils.scraper import scrape_all_sources

class Command(BaseCommand):
    help = 'Scrape and populate mental health blogs from top web portals and RSS feeds'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Fetching and scraping wellness articles from authoritative web sources..."))
        
        articles = scrape_all_sources()
        added_count = 0
        skipped_count = 0

        for entry in articles:
            blog, created = Blog.objects.get_or_create(
                title=entry['title'],
                defaults={
                    'summary': entry['summary'],
                    'link': entry.get('link'),
                    'category': entry.get('category', 'General'),
                    'source': entry.get('source', 'ACROCARE Wellness'),
                    'read_time': entry.get('read_time', '3 min read'),
                    'image_url': entry.get('image_url'),
                }
            )
            if created:
                added_count += 1
                try:
                    self.stdout.write(self.style.SUCCESS(f"  [+] Added: [{blog.category}] {blog.title[:60]}... ({blog.source})"))
                except Exception:
                    pass
            else:
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(f"\nSuccessfully processed feeds: {added_count} new articles added, {skipped_count} existing skipped."))
        self.stdout.write(self.style.SUCCESS(f"Total blogs in database: {Blog.objects.count()}"))
