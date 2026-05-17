import requests
import feedparser
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

FEED_URL = "https://ledlamba.com/feed"
OUTPUT_DIR = "posts"
BASE_URL = "https://ledlamba.com"

def clean_filename(title):
    title = re.sub(r'[^\w\s-]', '', title)
    title = re.sub(r'[-\s]+', '-', title)
    return title.strip('-').lower()[:80]

def process_links_to_anchor(content_html, base_url):
    soup = BeautifulSoup(content_html, 'html.parser')
    links_data = []
    
    for a_tag in soup.find_all('a', href=True):
        original_href = a_tag['href']
        link_text = a_tag.get_text(strip=True)
        
        if original_href.startswith('/'):
            absolute_url = urljoin(base_url, original_href)
        elif not original_href.startswith(('http://', 'https://', 'mailto:', 'tel:', '#')):
            absolute_url = urljoin(base_url, original_href)
        else:
            absolute_url = original_href
        
        a_tag['data-original-url'] = absolute_url
        a_tag['data-archive-link'] = "true"
        a_tag['href'] = "#"
        a_tag['onclick'] = "return false;"
        a_tag['title'] = f"Orijinal: {absolute_url}"
        
        links_data.append({
            'text': link_text,
            'url': absolute_url
        })
    
    return str(soup), links_data

def create_markdown_file(title, link, published, summary, content_html, links_data, slug):
    soup_archived = BeautifulSoup(content_html, 'html.parser')
    archived_html, _ = process_links_to_anchor(str(soup_archived), BASE_URL)
    
    content_for_md = archived_html
    content_for_md = re.sub(r'>\s+<', '><', content_for_md)
    content_for_md = re.sub(r'\n\s*\n', '\n\n', content_for_md)
    
    links_md = ""
    if links_data:
        links_md = "\n## İçerikteki Linkler\n\n"
        for link in links_data:
            links_md += f'- <a href="#" data-original-url="{link["url"]}" data-archive-link="true" onclick="return false;" title="Orijinal: {link["url"]}">{link["text"]}</a>\n'
        links_md += "\n"
    
    md_content = f"""---
title: "{title}"
date: "{published}"
canonical_url: "{link}"
original_url: "{link}"
source: "ledlamba.com"
archive_date: "{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
total_links: {len(links_data)}
---

# {title}

> **Arşiv Notu:** Bu içerik [ledlamba.com](https://ledlamba.com) adresinden arşiv amaçlı çekilmiştir.  
> **Orijinal URL:** {link}  
> **Yayınlanma:** {published}  
> **Arşivlenme:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{content_for_md}

---

{links_md}
---

<link rel="canonical" href="{link}" />

<!-- 
  ARŞİV BİLGİSİ
  - Bu dosya ledlamba.com'dan arşiv amaçlı çekilmiştir.
  - Tüm linkler anchor formatına çevrilmiştir (tıklanamaz).
  - Orijinal URL'ler data-original-url özelliğinde korunmaktadır.
  - Asıl kaynak: {link}
-->
"""
    return md_content

def fetch_posts():
    print(f"Feed çekiliyor: {FEED_URL}")
    
    response = requests.get(FEED_URL, timeout=30, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    response.raise_for_status()
    
    feed = feedparser.parse(response.content)
    
    if not feed.entries:
        print("Hiç yazı bulunamadı!")
        return
    
    print(f"Toplam {len(feed.entries)} yazı bulundu.")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    archive_posts = []
    
    for entry in feed.entries:
        title = entry.get('title', 'Untitled')
        link = entry.get('link', '')
        published = entry.get('published', '')
        summary = entry.get('summary', '')
        content_html = entry.get('content', [{}])[0].get('value', summary) if 'content' in entry else summary
        
        _, links_data = process_links_to_anchor(content_html, BASE_URL)
        
        slug = clean_filename(title)
        filename = f"{slug}.md"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        md_content = create_markdown_file(title, link, published, summary, content_html, links_data, slug)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        archive_posts.append({
            'title': title,
            'slug': slug,
            'filename': filename,
            'link': link,
            'published': published,
            'total_links': len(links_data)
        })
        
        print(f"Arşivlendi: {filename} | Linkler: {len(links_data)} | {title[:50]}...")
    
    index_content = f"""# Led Lamba Blog Arşivi

> **Arşiv Oluşturulma:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
> **Kaynak:** [ledlamba.com](https://ledlamba.com)  
> **Toplam Yazı:** {len(archive_posts)}

---

| # | Başlık | Yayınlanma | Orijinal | Link Sayısı |
|---|--------|-----------|----------|-------------|
"""
    for i, post in enumerate(archive_posts, 1):
        index_content += f"| {i} | [{post['title']}](./{post['filename']}) | {post['published']} | [Git]({post['link']}) | {post['total_links']} |\n"
    
    index_content += f"""
---

## Arşiv Hakkında

Bu arşivdeki tüm yazılar `.md` (Markdown) formatında saklanmaktadır.  
Her yazının içindeki linkler **anchor formatına** çevrilmiştir (`href="#"`).  
Orijinal URL'ler `data-original-url` özelliğinde korunmaktadır.

---

<link rel="canonical" href="https://ledlamba.com" />
"""
    
    with open(os.path.join(OUTPUT_DIR, 'index.md'), 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print(f"\n✅ Arşiv tamamlandı!")
    print(f"📁 Toplam {len(archive_posts)} yazı arşivlendi.")
    print(f"📋 Arşiv indeksi: posts/index.md")

if __name__ == "__main__":
    fetch_posts()
