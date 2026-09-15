import logging

from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest

from .models import Blog
from .utils.utils import fetch_rss_articles
from .blog_feed import fetch_all_feeds

logger = logging.getLogger(__name__)


def blog_list(request):
    blogs = Blog.objects.all().order_by('-created_at')
    return render(request, 'blog/blog_list.html', {'blogs': blogs})


def blog_list_external(request):
    external_articles = fetch_rss_articles()
    return render(request, 'blog/blog_external.html', {'external_articles': external_articles})


def blog_view(request):
    articles = fetch_all_feeds()

    categories = {}
    for article in articles:
        cat = article['category']
        categories.setdefault(cat, []).append(article)

    return render(request, "blog/blog_list.html", {
        'categories': categories
    })


def blog_redirect(request):
    link = request.GET.get('link')
    title = request.GET.get('title')

    if not link:
        return HttpResponseBadRequest("Missing 'link' parameter.")

    blog, _ = Blog.objects.get_or_create(link=link, defaults={'title': title or 'Untitled'})
    blog.views += 1
    blog.save()
    return redirect(link)
