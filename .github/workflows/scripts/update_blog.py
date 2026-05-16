#!/usr/bin/env python3
"""
Sietra Elektrik - Blog Otomasyon Scripti
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
    return {'last_publish_date': '', 'daily_count': 0, 'published_queue': [], 'queue_position': 0}

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

def fetch_wp_content(url):
    try:
        slug = url.rstrip('/').split('/')[-1]
        api_url = f"https://ledlamba.com/wp-json/wp/v2/posts?slug={slug}&_embed"
        
        print(f"📄 WP API ile icerik cekiliyor: {slug}")
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if data and len(data) > 0:
            post = data[0]
            content_html = post.get('content', {}).get('rendered', '')
            
            if content_html:
                content = re.sub(r'<script.*?</script>', '', content_html, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<style.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
                
                def fix_anchor(m):
                    href = re.search(r'href="([^"]*)"', m.group(0))
                    text = re.sub(r'<[^>]+>', '', m.group(0))
                    return f'[{text.strip()}]({href.group(1)})' if href and text.strip() else text
                
                content = re.sub(r'<a[^>]*>.*?</a>', fix_anchor, content, flags=re.DOTALL | re.IGNORECASE)
                
                def fix_img(m):
                    src = re.search(r'src="([^"]*)"', m.group(0))
                    alt = re.search(r'alt="([^"]*)"', m.group(0))
                    return f'![{alt.group(1) if alt else "Resim"}]({src.group(1) if src else ""})'
                
                content = re.sub(r'<img[^>]*>', fix_img, content, flags=re.IGNORECASE)
                
                content = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<h4[^>]*>(.*?)</h4>', r'#### \1', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<br\s*/?>', '\n', content, flags=re.IGNORECASE)
                content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', content, flags=re.DOTALL | re.IGNORECASE)
                
                content = re.sub(r'<th[^>]*>(.*?)</th>', r'| \1 ', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<td[^>]*>(.*?)</td>', r'| \1 ', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<tr[^>]*>(.*?)</tr>', r'\1|\n', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<thead[^>]*>.*?</thead>', '', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<tbody[^>]*>(.*?)</tbody>', r'\1', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<table[^>]*>(.*?)</table>', r'\1\n', content, flags=re.DOTALL | re.IGNORECASE)
                
                content = re.sub(r'<[^>]+>', '', content)
                content = html.unescape(content)
                content = re.sub(r'\n\s*\n', '\n\n', content)
                content = re.sub(r'\n{3,}', '\n\n', content)
                return content.strip()
        
        return ""
    except Exception as e:
        print(f"⚠️ WP API hatasi ({url}): {e}")
        return ""

def parse_rss(xml_content):
    if not xml_content:
        return []
    
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        print(f"❌ XML parse hatasi: {e}")
        return []
    
    ns = {'content': 'http://purl.org/rss/1.0/modules/content/', 'dc': 'http://purl.org/dc/elements/1.1/'}
    items = []
    
    for item in root.findall('.//item'):
        title_elem = item.find('title')
        link_elem = item.find('link')
        pub_date_elem = item.find('pubDate')
        creator_elem = item.find('dc:creator', ns)
        desc_elem = item.find('description')
        
        title = html.unescape(title_elem.text) if title_elem is not None and title_elem.text else ''
        link = link_elem.text if link_elem is not None and link_elem.text else ''
        pub_date = pub_date_elem.text if pub_date_elem is not None and pub_date_elem.text else ''
        creator = html.unescape(creator_elem.text) if creator_elem is not None and creator_elem.text else 'Muslim SEVINDIK'
        description = html.unescape(desc_elem.text) if desc_elem is not None and desc_elem.text else ''
        
        try:
            date_obj = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
            formatted_date = date_obj.strftime('%Y-%m-%d')
            display_date = date_obj.strftime('%d %B %Y')
        except:
            formatted_date = pub_date[:10] if pub_date else ''
            display_date = pub_date
        
        slug = re.sub(r'[^\w\s-]', '', title).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)[:60]
        
        items.append({
            'title': title, 'link': link, 'pub_date': pub_date,
            'formatted_date': formatted_date, 'display_date': display_date,
            'creator': creator, 'description': description, 'content': '', 'slug': slug
        })
    
    return items

def create_archive_file(item):
    filename = f"{item['formatted_date']}-{item['slug']}.md"
    filepath = os.path.join(ARCHIVE_DIR, filename)
    
    if os.path.exists(filepath):
        return filepath, False
    
    if not item.get('content'):
        item['content'] = fetch_wp_content(item['link'])
    
    content_text = item['content'] if item['content'] else item['description']
    
    content = f"""# {item['title']}

**Yazar:** {item['creator']}  
**Yayin Tarihi:** {item['display_date']}  
**Orijinal Kaynak:** [{item['link']}]({item['link']})

---

{content_text}

---

> Bu icerik, SEO arsivleme amaciyla [ledlamba.com](https://ledlamba.com) blogundan otomatik olarak arsivlenmistir.  
> Orijinal icerige yukaridaki baglantidan ulasabilirsiniz.

---

## Canonical Link

<link rel="canonical" href="{item['link']}" />

**Orijinal Blog Linki:** {item['link']}

---

*Arsivlenme Tarihi: {datetime.now().strftime('%Y-%m-%d')}*
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath, True

def copy_to_published(item, archive_path):
    filename = os.path.basename(archive_path)
    dest_path = os.path.join(PUBLISHED_DIR, filename)
    
    if os.path.exists(dest_path):
        return dest_path, False
    
    with open(archive_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return dest_path, True

def generate_blog_table(items):
    lines = ["| # | Tarih | Baslik |", "|---|-------|--------|"]
    
    for i, item in enumerate(items[:MAX_POSTS]):
        clean_title = item['title'].replace('|', '\\|')
        linked_title = f"[{clean_title}]({item['link']})"
        lines.append(f"| {i+1} | {item['formatted_date']} | {linked_title} |")
    
    return "\n".join(lines)

def update_readme(items):
    try:
        with open(README_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        content = generate_default_readme()
    
    blog_table = generate_blog_table(items)
    
    new_section = f"""### ✍️ Son Blog Yazilarim

{blog_table}

> 🔗 Tum yazilar [ledlamba.com/faydali-bilgiler](https://ledlamba.com/faydali-bilgiler) adresinde yayinlanmaktadir.  
> 🔄 Son guncelleme: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC
"""
    
    if '### ✍️ Son Blog Yazilarim' in content:
        pattern = r'(### ✍️ Son Blog Yazilarim.*?)(?=### |## |---|$)'
        content = re.sub(pattern, new_section + "\n\n", content, flags=re.DOTALL, count=1)
    else:
        content = content.replace(
            "### 📩 Iletisim & Is Birligi",
            new_section + "\n---\n\n### 📩 Iletisim & Is Birligi"
        )
    
    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {README_PATH} guncellendi ({len(items[:MAX_POSTS])} yazi)")

def generate_default_readme():
    return """# Muslim Sevindik | Sietra Elektrik

**LED Aydinlatma Uzmani, Enerji Arastirmacisi ve Sietra Elektrik Kurucusu.**

---

### 🚀 One Cikan Projeler & Uzmanlik Alanlari
- **GOZYUMMAZ:** Akilli guvenlik ve konutsal aydinlatma ekosistemi.
- **IoT & DALI/D4i:** Yeni nesil dijital aydinlatma protokolleri.
- **Enerji Stratejileri:** Dagitik altyapilar ve yenilenebilir enerji.

---

### 📚 Teknik Rehberler & Faydali Bilgiler
👉 **[ledlamba.com - Faydali Bilgiler](https://ledlamba.com/faydali-bilgiler)**

---

### 🎓 Akademik & Sektorel Otorite
- 🏛️ **Google Scholar:** [Akademik Yayinlar](https://scholar.google.com.tr/citations?user=Z1LgdF0AAAAJ)
- ⚡ **Energy Central:** [Sektorel Makaleler](https://www.energycentral.com/member/QYZQf5E2VJ)
- 💻 **GitHub:** [Teknik Projeler](https://github.com/sietraelektrik-byte)

---

### 📩 Iletisim & Is Birligi
- **Web Sitesi:** [ledlamba.com](https://ledlamba.com)
- **E-posta:** sietraelektrik@gmail.com
- **Konum:** Tekirdag, Turkiye
"""

def update_feed_xml(items, daily_items):
    now_str = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
    
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<rss version="2.0"')
    lines.append('    xmlns:content="http://purl.org/rss/1.0/modules/content/"')
    lines.append('    xmlns:dc="http://purl.org/dc/elements/1.1/">')
    lines.append('    <channel>')
    lines.append('        <title>Sietra Elektrik - LED Aydinlatma Blog Arsivi</title>')
    lines.append('        <link>https://github.com/sietraelektrik-byte</link>')
    lines.append('        <description>ledlamba.com blog yazilarinin GitHub arsivi - Gunluk 2 yazi</description>')
    lines.append(f'        <lastBuildDate>{now_str}</lastBuildDate>')
    lines.append('        <language>tr</language>')
    lines.append(f'        <itemCount>{len(daily_items)}</itemCount>')
    
    for item in daily_items:
        if not item.get('content'):
            item['content'] = fetch_wp_content(item['link'])
        
        lines.append('        <item>')
        lines.append(f'            <title>{html.escape(item["title"])}</title>')
        lines.append(f'            <link>{item["link"]}</link>')
        lines.append(f'            <pubDate>{item.get("pub_date", "")}</pubDate>')
        lines.append(f'            <dc:creator>{html.escape(item["creator"])}</dc:creator>')
        lines.append(f'            <guid isPermaLink="true">{item["link"]}</guid>')
        
        content_text = item['content'] if item['content'] else item.get('description', '')
        lines.append(f'            <content:encoded><![CDATA[{content_text}]]></content:encoded>')
        lines.append('        </item>')
    
    lines.append('    </channel>')
    lines.append('</rss>')
    
    with open(FEED_XML_PATH, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    print(f"✅ {FEED_XML_PATH} guncellendi ({len(daily_items)} gunluk yazi)")

def get_daily_posts(items, state):
    today = datetime.now().strftime('%Y-%m-%d')
    
    if state['last_publish_date'] != today:
        state['daily_count'] = 0
        state['last_publish_date'] = today
    
    all_links = [item['link'] for item in items]
    unpublished = [link for link in all_links if link not in state['published_queue']]
    
    if not unpublished:
        print("🔄 Tum yazilar paylasildi, kuyruk sifirlaniyor...")
        state['published_queue'] = []
        state['queue_position'] = 0
        unpublished = all_links
    
    start_pos = state['queue_position'] % len(items)
    daily_links = []
    
    for i in range(len(items)):
        idx = (start_pos + i) % len(items)
        link = items[idx]['link']
        if link not in state['published_queue'] and link not in daily_links:
            daily_links.append(link)
        if len(daily_links) >= DAILY_LIMIT:
            break
    
    daily_items = [item for item in items if item['link'] in daily_links]
    
    for link in daily_links:
        if link not in state['published_queue']:
            state['published_queue'].append(link)
    
    state['queue_position'] = (state['queue_position'] + len(daily_links)) % len(items)
    state['daily_count'] += len(daily_links)
    
    return daily_items, state

def main():
    print("="*70)
    print("🚀 SIETRA ELEKTRIK - BLOG OTOMASYON SISTEMI")
    print("="*70)
    print()
    
    state = load_state()
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    os.makedirs(PUBLISHED_DIR, exist_ok=True)
    
    xml_content = fetch_rss()
    if not xml_content:
        print("❌ RSS alinamadi, islem sonlandiriliyor.")
        return
    
    items = parse_rss(xml_content)
    print(f"📰 Toplam {len(items)} yazi bulundu.")
    print()
    
    if not items:
        print("⚠️ Hic yazi bulunamadi.")
        return
    
    print("-"*70)
    print("📂 ARSIVLEME (Tam Icerik - WP REST API)")
    print("-"*70)
    
    new_count = 0
    for item in items:
        archive_path, is_new = create_archive_file(item)
        if is_new:
            print(f"📄 Yeni arsiv: {os.path.basename(archive_path)}")
            new_count += 1
        copy_to_published(item, archive_path)
    
    print(f"✅ {len(items)} toplam yazi arsivlendi ({new_count} yeni)")
    print()
    
    print("-"*70)
    print("📝 README GUNCELLEME")
    print("-"*70)
    update_readme(items)
    print()
    
    print("-"*70)
    print("📤 GUNLUK YAZI SECIMI")
    print("-"*70)
    
    daily_items, state = get_daily_posts(items, state)
    
    print(f"📋 Bugun paylasilacak {len(daily_items)} yazi:")
    for i, item in enumerate(daily_items, 1):
        print(f"   {i}. {item['title'][:60]}...")
    print()
    
    print("-"*70)
    print("🌐 FEED.XML GUNCELLEME (Tam Icerik)")
    print("-"*70)
    update_feed_xml(items, daily_items)
    print()
    
    save_state(state)
    
    print("="*70)
    print("🎉 ISLEM TAMAMLANDI!")
    print("="*70)
    print(f"   📚 Toplam arsivlenen yazi: {len(items)}")
    print(f"   📄 Yeni eklenen yazi: {new_count}")
    print(f"   📤 Gunluk paylasim: {len(daily_items)} yazi")
    print(f"   📊 Toplam paylasilan: {len(state['published_queue'])}")
    print(f"   📍 Siradaki pozisyon: {state['queue_position']}")
    print(f"   📅 Son calistirma: {state['last_publish_date']}")
    print()
    print("   Platformlar su adresi RSS feed olarak ekleyebilir:")
    print("   👉 https://raw.githubusercontent.com/sietraelektrik-byte/sietraelektrik-byte/main/feed.xml")
    print("="*70)

if __name__ == '__main__':
    main()
