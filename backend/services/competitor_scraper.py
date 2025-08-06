import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
from datetime import datetime
from typing import List, Dict

def scrape_competitor(url: str) -> dict:
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception:
        return {"error": "Failed to fetch or parse the URL."}

    # Try to find articles/posts
    articles = soup.find_all(['article'])
    if not articles:
        # Fallback: look for common blog post containers
        articles = soup.find_all(['h2', 'h3'])

    posts = []
    title_words = []
    dates = []
    for art in articles:
        # Try to extract title
        title = None
        link = None
        date = None
        # Article tag
        if art.name == 'article':
            # Title
            h = art.find(['h1', 'h2', 'h3'])
            if h:
                title = h.get_text(strip=True)
            # Link
            a = art.find('a', href=True)
            if a:
                link = a['href']
            # Date
            time_tag = art.find('time')
            if time_tag and time_tag.has_attr('datetime'):
                date = time_tag['datetime']
            elif time_tag:
                date = time_tag.get_text(strip=True)
        else:
            # Fallback for h2/h3
            title = art.get_text(strip=True)
            a = art.find('a', href=True)
            if a:
                link = a['href']
        if title:
            title_words.extend(re.findall(r'\w+', title.lower()))
        posts.append({
            "title": title or "",
            "url": link or url,
            "date": date or None
        })
        if date:
            try:
                dates.append(datetime.fromisoformat(date[:19]))
            except Exception:
                pass
    # Stats
    total_posts = len(posts)
    avg_title_length = int(sum(len(p['title'].split()) for p in posts) / total_posts) if total_posts else 0
    # Posting frequency
    estimated_frequency = None
    if len(dates) > 1:
        dates.sort()
        days = (dates[-1] - dates[0]).days or 1
        freq = total_posts / days
        if freq >= 1:
            estimated_frequency = f"{freq:.1f} posts/day"
        else:
            estimated_frequency = f"{(7*freq):.1f} posts/week"
    else:
        estimated_frequency = "Unknown"
    # Top keywords
    stopwords = set(['the','and','of','to','in','a','for','on','with','at','by','an','is','from','as','it','that','this','be','are','was','or','but','not','your','you','we','our'])
    keywords = [w for w in title_words if w not in stopwords and len(w) > 2]
    top_keywords = [w for w, _ in Counter(keywords).most_common(5)]
    return {
        "total_posts": total_posts,
        "avg_title_length": avg_title_length,
        "estimated_frequency": estimated_frequency,
        "top_keywords": top_keywords,
        "posts": posts
    } 