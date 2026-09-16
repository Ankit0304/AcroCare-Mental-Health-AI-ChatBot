import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from django.http import HttpResponseBadRequest

from .models import Blog
from .utils.scraper import scrape_all_sources, estimate_read_time

logger = logging.getLogger(__name__)

def is_staff_user(user):
    """Check if the user is logged in and has staff/admin privileges."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def blog_list(request):
    """
    Main wellness articles & blog directory view.
    Supports search (?q=...), category filtering (?category=...), and ordering.
    """
    # Auto-seed if database is empty on first load
    if Blog.objects.count() == 0:
        try:
            articles = scrape_all_sources()
            for entry in articles:
                Blog.objects.get_or_create(
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
        except Exception as e:
            logger.warning(f"Auto-seed blogs failed: {e}")

    query = request.GET.get('q', '').strip()
    selected_category = request.GET.get('category', 'All').strip()

    blogs_qs = Blog.objects.all()

    # Search filter
    if query:
        blogs_qs = blogs_qs.filter(
            Q(title__icontains=query) |
            Q(summary__icontains=query) |
            Q(category__icontains=query) |
            Q(source__icontains=query)
        )

    # Category filter
    if selected_category and selected_category.lower() != 'all':
        blogs_qs = blogs_qs.filter(category__iexact=selected_category)

    # Available categories
    all_categories = [
        'All',
        'Anxiety',
        'Mindfulness',
        'Depression',
        'Sleep',
        'Stress Relief',
        'Self-Care',
        'General'
    ]

    context = {
        'blogs': blogs_qs,
        'categories': all_categories,
        'selected_category': selected_category,
        'query': query,
        'total_count': blogs_qs.count(),
        'is_admin': is_staff_user(request.user),
    }
    return render(request, 'blog/blog_list.html', context)


@user_passes_test(is_staff_user, login_url='login')
def blog_create(request):
    """
    Admin-only interface to compose and publish custom wellness articles.
    """
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        summary = request.POST.get('summary', '').strip()
        content = request.POST.get('content', '').strip()
        category = request.POST.get('category', 'General').strip()
        source = request.POST.get('source', 'ACROCARE Editorial').strip()
        image_url = request.POST.get('image_url', '').strip()
        link = request.POST.get('link', '').strip() or None

        if not title or not summary:
            messages.error(request, "Please provide both a title and summary for the article.")
            return render(request, 'blog/blog_create.html')

        read_time = estimate_read_time(content or summary)

        blog = Blog.objects.create(
            title=title,
            summary=summary,
            content=content,
            category=category,
            source=source or 'ACROCARE Editorial',
            read_time=read_time,
            image_url=image_url or None,
            link=link,
            author=request.user,
        )
        messages.success(request, f"Article '{blog.title}' published successfully!")
        return redirect('blog_list')

    return render(request, 'blog/blog_create.html', {
        'categories': ['Anxiety', 'Mindfulness', 'Depression', 'Sleep', 'Stress Relief', 'Self-Care', 'General']
    })


@user_passes_test(is_staff_user, login_url='login')
def sync_web_blogs(request):
    """
    Admin-only action to trigger live web scraping & feed parsing.
    """
    try:
        articles = scrape_all_sources()
        added_count = 0
        for entry in articles:
            _, created = Blog.objects.get_or_create(
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

        messages.success(request, f"Web sync complete! Added {added_count} new wellness articles from web sources.")
    except Exception as e:
        logger.error(f"Error syncing web feeds: {e}")
        messages.error(request, f"Failed to sync web feeds: {e}")

    return redirect('blog_list')


def blog_detail(request, blog_id):
    """View full article content or redirect if external link."""
    blog = get_object_or_404(Blog, id=blog_id)
    
    # If external link without local full content, redirect out
    if blog.link and not blog.content:
        return redirect(blog.link)

    return render(request, 'blog/blog_detail.html', {'blog': blog})


def blog_redirect(request):
    """Click redirect for external web links."""
    link = request.GET.get('link')

    if not link:
        return HttpResponseBadRequest("Missing 'link' parameter.")

    return redirect(link)
