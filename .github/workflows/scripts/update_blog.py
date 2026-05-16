#!/usr/bin/env python3
"""
Sietra Elektrik - Blog Otomasyon Scripti
Bu script GitHub Actions icinde calisir
"""

import requests
import xml.etree.ElementTree as ET
import re
import html
import os
import json
from datetime import datetime

FEED_URL = 'https://ledlamba.com/feed'
README_PATH = 'README.md'
ARCHIVE_DIR = 'blog-archive'
PUBLISHED_DIR = 'published_posts'
FEED_XML_PATH = 'feed.xml'
STATE_FILE = 'scripts/publish_state.json'
MAX_POSTS = 10
DAILY_LIMIT = 2

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'last_publish_date': '',
        'daily_count': 0,
        'published_queue': [],
        'queue_position': 0
    }

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def fetch_rss():
    try:
        print(f"📡 {FEED_URL} adresinden veri cekiliyor...")
        response = requests.get(FEED_URL, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"❌ RSS cekme hatasi: {e}")
        return None

def fetch_full_content(url):
    """Yazinin tam icerigini sayfasindan ceker."""
    try:
        print(f"📄 Icerik cekiliyor: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        html_text = response.text
        
        # Yontem 1: <article> etiketi icindeki icerik (ledlamba.com yapisi)
        article_match = re.search(
            r'<article[^>]*>(.*?)</article>',
            html_text,
            re.DOTALL | re.IGNORECASE
        )
        
        if article_match:
            content = article_match.group(1)
            # Sadece metin icerigini
