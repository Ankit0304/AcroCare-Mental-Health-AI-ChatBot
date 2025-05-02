from django.shortcuts import render
from .models import Blog

def blog_list(request):
    blogs = Blog.objects.all().order_by('-created_at')
    # blogs = Blog.objects.all().order_by('-id')
    return render(request, 'blog/blog_list.html', {'blogs': blogs})


from .utils.utils import fetch_rss_articles  # 👈 Import the function

def blog_list_external(request):
    external_articles = fetch_rss_articles()
    return render(request, 'blog/blog_external.html', {'external_articles': external_articles})

from .blog_feed import fetch_all_feeds
def blog_view(request):
    articles = fetch_all_feeds()

    categories = {}
    for article in articles:
        cat = article['category']
        categories.setdefault(cat, []).append(article)

    return render(request, "blogs/blog_list.html", {
        'categories': categories
    })


from django.shortcuts import redirect
from .models import Blog

def blog_redirect(request):
    link = request.GET.get('link')
    title = request.GET.get('title')

    if link:
        blog, _ = Blog.objects.get_or_create(link=link, defaults={'title': title})
        blog.views += 1
        blog.save()
        return redirect(link)
