import feedparser

# Add categories manually for now — or later extract from keywords/tags
def categorize_article(title, summary):
    title = title.lower()
    summary = summary.lower()

    if 'anxiety' in title or 'anxiety' in summary:
        return 'Anxiety'
    elif 'depression' in title or 'depression' in summary:
        return 'Depression'
    elif 'stress' in title or 'burnout' in summary:
        return 'Stress'
    elif 'productivity' in title or 'focus' in summary:
        return 'Productivity'
    else:
        return 'General'

def fetch_all_feeds():
    urls = [
        "https://www.mentalhealth.org.uk/rss.xml",
        "https://rss.app/feeds/YOUR_EARKICK_FEED_ID.xml",  # replace with your RSS feed
    ]

    all_articles = []
    for url in urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            category = categorize_article(entry.title, entry.get('summary', ''))
            all_articles.append({
                'title': entry.title,
                'link': entry.link,
                'summary': entry.get('summary', '')[:150] + "...",
                'published': entry.get('published', ''),
                'category': category,
            })

    return sorted(all_articles, key=lambda x: x['published'], reverse=True)
