import feedparser

def fetch_rss_articles():
    rss_url = "https://www.mentalhealth.org.uk/rss.xml"  # Example RSS feed
    feed = feedparser.parse(rss_url)

    articles = []
    for entry in feed.entries[:6]:
        articles.append({
            'title': entry.title,
            'link': entry.link,
            'summary': entry.summary,
            'published': entry.published,
        })

    return articles
