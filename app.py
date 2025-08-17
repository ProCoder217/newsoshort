import feedparser
import requests
from bs4 import BeautifulSoup
import re
from flask import Flask, jsonify, render_template, request, session, redirect, url_for, Response ,stream_with_context
from functools import wraps
import json
import time
import os

# --- Correct import from your existing summarizer file ---
from summarizer import give_summary, SUBGENRES

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-super-secret-key-that-you-should-definitely-change'

# --- Hardcoded User Database ---
if not os.path.isfile("users.json"):
	with open("users.json","w") as f:
		json.dump({},f)

# --- Configuration ---
RSS_FEEDS = {
    "Automobile": "https://www.autocarindia.com/rss/all",
    "Business": "https://www.thehindu.com/business/feeder/default.rss",
    "Entertainment": "https://www.thehindu.com/entertainment/feeder/default.rss",
    "Environment": "https://www.sciencedaily.com/rss/top/environment.xml",
    "Finance": "https://indianexpress.com/section/business/banking-and-finance/feed/",
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

# --- Helper Functions ---
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
    date_time_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}(?:\s+\d{1,2}:\d{2}\s+(?:am|pm)\s+IST)?'
    epaper_pattern = r'e-Paper Published -.*?\s+IST'
    copyright_pattern = r'Copyright©.*?\.?'
    topics_pattern = r'technology \(general\).*?$'
    cleaned_text = re.sub(date_time_pattern, '', text, flags=re.IGNORECASE)
    cleaned_text = re.sub(epaper_pattern, '', cleaned_text, flags=re.IGNORECASE)
    cleaned_text = re.sub(copyright_pattern, '', cleaned_text, flags=re.IGNORECASE)
    cleaned_text = re.sub(topics_pattern, '', cleaned_text, flags=re.IGNORECASE)
    return cleaned_text.strip()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_user():
    return dict(username=session.get('username'))

# --- Main Routes ---
@app.route('/')
def index():
    return render_template('index.html', categories=RSS_FEEDS.keys())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        USERS=json.load(open("users.json"))
        user = USERS.get(username)
        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('index'))
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        USERS=json.load(open("users.json"))
        if username in USERS:
            return render_template('register.html', error="User already exists")
        USERS[username] = {"password": password, "bookmarks": []}
        with open("users.json","w") as f:
        	json.dump(USERS,f)
        session['username'] = username
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/bookmarks')
@login_required
def bookmarks():
    USERS=json.load(open("users.json"))
    user_bookmarks = USERS[session['username']]['bookmarks']
    with open("users.json","w") as f:
    	json.dump(USERS,f)
    return render_template('bookmarks.html', all_categories=RSS_FEEDS.keys(), user_bookmarks=user_bookmarks)

@app.route('/for_you')
@login_required
def for_you():
    all_categories = list(RSS_FEEDS.keys())
    return render_template('for_you.html', all_categories=all_categories)

@app.route('/news/<category>')
def news(category):
    if category not in RSS_FEEDS:
        return "Category not found", 404
    all_categories = list(RSS_FEEDS.keys())
    return render_template('news.html', category=category, all_categories=all_categories)

# --- API Routes ---
def process_feed_entry(entry, category):
    article_text = extract_article_text(entry.link)
    if not article_text or len(article_text.split()) < 50:
        return None
    cleaned_text = clean_article_text(article_text)
    result = give_summary(cleaned_text, category)
    safe_subgenre = result.subgenre if result.subgenre in ALL_SUBGENRES else "Default"
    img_subgenre = safe_subgenre.replace(" ", "_")
    return {
        "title": entry.title, "summary": result.summary, "link": entry.link,
        "subgenre": safe_subgenre, "img_subgenre": img_subgenre
    }

@app.route('/api/get_news')
def api_get_news():
    category = request.args.get('category')
    page = int(request.args.get('page', 1))
    if not category or category not in RSS_FEEDS:
        return jsonify({"error": "Invalid category"}), 400
    feed = feedparser.parse(RSS_FEEDS[category])
    items_per_page = 5
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    entries = feed.entries[start_index:end_index]
    news_items = [item for entry in entries if (item := process_feed_entry(entry, category)) is not None]
    return jsonify(news_items)

# In app.py


@app.route('/api/get_news_for_you')
@login_required
def api_get_news_for_you():
    """
    API endpoint to fetch a paginated, mixed list of news from all 
    of a user's bookmarked categories, sorted chronologically.
    """
    USERS = json.load(open("users.json"))
    user_bookmarks = USERS.get(session['username'], {}).get('bookmarks', [])
    page = int(request.args.get('page', 1))
    
    if not user_bookmarks:
        return jsonify([])

    all_entries = []
    # Step 1: Gather all entries from all bookmarked feeds
    for category in user_bookmarks:
        try:
            feed_url = RSS_FEEDS.get(category)
            if not feed_url:
                continue
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                # Add metadata needed for processing and sorting
                entry['source_category'] = category
                # Use published_parsed for sorting, with a fallback to the current time
                entry['sort_timestamp'] = time.mktime(entry.published_parsed) if hasattr(entry, 'published_parsed') else time.time()
            all_entries.extend(feed.entries)
        except Exception as e:
            print(f"Could not process feed for {category}: {e}")
            continue

    # Step 2: Sort the combined list by timestamp (newest first)
    all_entries.sort(key=lambda x: x.get('sort_timestamp', 0), reverse=True)

    # Step 3: Paginate the sorted list
    items_per_page = 5  # Keep this consistent with /api/get_news
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    
    entries_for_page = all_entries[start_index:end_index]

    # Step 4: Process only the entries for the current page to be efficient
    news_items = []
    for entry in entries_for_page:
        category_of_entry = entry.get('source_category')
        processed_item = process_feed_entry(entry, category_of_entry)
        if processed_item:
            news_items.append(processed_item)
            
    return jsonify(news_items)
	
@app.route('/api/toggle_bookmark', methods=['POST'])
@login_required
def toggle_bookmark():
    category = request.json.get('category')
    if not category or category not in RSS_FEEDS:
        return jsonify({"success": False, "error": "Invalid category"}), 400

    # Use a safer read-modify-write pattern for the JSON file
    with open("users.json", "r+") as f:
        USERS = json.load(f)
        user_bookmarks = USERS[session['username']]['bookmarks']

        if category in user_bookmarks:
            user_bookmarks.remove(category)
            action = 'removed'
        else:
            user_bookmarks.append(category)
            action = 'added'
        
        # Go back to the start of the file to overwrite it with updated data
        f.seek(0)
        json.dump(USERS, f, indent=4) # Using indent for readability
        f.truncate()

    return jsonify({"success": True, "action": action, "bookmarks": user_bookmarks})
if __name__ == '__main__':
    app.run("0.0.0.0")

