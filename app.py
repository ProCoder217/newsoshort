import feedparser
import requests
from bs4 import BeautifulSoup
import re
from flask import Flask, jsonify, render_template, request
from summarizer import give_summary, SUBGENRES

app = Flask(__name__)

# --- CONFIGURATION ---
RSS_FEEDS = {
    "Automobile": "https://www.autocarindia.com/rss/all",
    "Business": "https://www.thehindu.com/business/feeder/default.rss",
    "Entertainment": "https://www.thehindu.com/entertainment/feeder/default.rss",
    "Environment": "https://www.sciencedaily.com/rss/top/environment.xml",
    "Finance": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
    "Health": "https://www.sciencedaily.com/rss/top/health.xml",
    "India": "https://www.thehindu.com/news/national/feeder/default.rss",
    "Lifestyle": "https://www.livemint.com/rss/opinion",
    "Opinion": "https://www.livemint.com/rss/opinion",
    "Politics": "https://www.livemint.com/rss/politics",
    "Science": "https://www.thehindu.com/sci-tech/science/feeder/default.rss",
    "Sports": "https://www.thehindu.com/sport/feeder/default.rss",
    "Technology": "https://www.livemint.com/rss/technology",
    "Travel": "https://www.thehindu.com/life-and-style/travel/feeder/default.rss",
    "World": "https://www.thehindu.com/news/international/feeder/default.rss",
}
ALL_SUBGENRES = list(SUBGENRES.keys())

def extract_article_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        return ' '.join(p.get_text() for p in paragraphs if p.get_text())
    except requests.RequestException:
        return ""

def clean_article_text(text):
    # Pattern to remove dates and times like "August 16, 2025 10:10 am IST"
    date_time_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}(?:\s+\d{1,2}:\d{2}\s+(?:am|pm)\s+IST)?'
    # Pattern to remove "e-Paper Published" and similar lines
    epaper_pattern = r'e-Paper Published -.*?\s+IST'
    # Pattern to remove "Copyright©" and similar lines
    copyright_pattern = r'Copyright©.*?\.?'
    # Pattern to remove topic/tags line
    topics_pattern = r'technology \(general\).*?$'

    cleaned_text = re.sub(date_time_pattern, '', text, flags=re.IGNORECASE)
    cleaned_text = re.sub(epaper_pattern, '', cleaned_text, flags=re.IGNORECASE)
    cleaned_text = re.sub(copyright_pattern, '', cleaned_text, flags=re.IGNORECASE)
    cleaned_text = re.sub(topics_pattern, '', cleaned_text, flags=re.IGNORECASE)

    return cleaned_text.strip()


# --- ROUTES ---
@app.route('/')
def index():
    """Renders the homepage with categories."""
    return render_template('index.html', categories=RSS_FEEDS.keys())

@app.route('/news/<category>')
def news(category):
    """Renders the news reel page."""
    if category not in RSS_FEEDS:
        return "Category not found", 404
    
    all_categories = list(RSS_FEEDS.keys())
    return render_template('news.html', category=category, all_categories=all_categories)

@app.route('/api/get_news')
def api_get_news():
    """API endpoint to fetch and summarize news."""
    category = request.args.get('category')
    page = int(request.args.get('page', 1))
    
    if not category or category not in RSS_FEEDS:
        return jsonify({"error": "Invalid category"}), 400

    feed = feedparser.parse(RSS_FEEDS[category])
    items_per_page = 1
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    entries = feed.entries[start_index:end_index]

    news_items = []
    for entry in entries:
        article_text = extract_article_text(entry.link)
        if not article_text or len(article_text.split()) < 50:
            continue
        
        # --- CLEAN THE TEXT BEFORE SUMMARIZING ---
        cleaned_text = clean_article_text(article_text)
        
        result = give_summary(cleaned_text, category)
        
        # --- THIS IS THE FIX ---
        # 1. Check if the original subgenre prediction is in our master list.
        if result.subgenre in ALL_SUBGENRES:
            safe_subgenre = result.subgenre
        else:
            # 2. If not, safely fall back to the main category name.
            safe_subgenre = "Default"
            
        # 3. Now, create the image name from the safe, validated subgenre.
        img_subgenre = safe_subgenre.replace(" ", "_")
        
        news_items.append({
            "title": entry.title,
            "summary": result.summary,
            "link": entry.link,
            "subgenre": safe_subgenre, # Use the safe subgenre for display
            "img_subgenre": img_subgenre # Use the final name for the image
        })
    
    return jsonify(news_items)

if __name__ == '__main__':
    app.run("0.0.0.0",debug=True)