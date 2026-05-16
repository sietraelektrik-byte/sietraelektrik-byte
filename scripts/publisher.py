import os
from datetime import datetime
import html
import re

# Yapılandırma
POSTS_DIR = "blog-archive"
PUBLISHED_DIR = "published_posts"
FEED_FILE = "feed.xml"
LIMIT = 2
BASE_URL = "https://ledlamba.com" # SEO için ana siten

def create_rss_feed(recent_files):
    rss_items = ""
    for file_name in recent_files:
        file_path = os.path.join(PUBLISHED_DIR, file_name)
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Başlığı dosyadan temizle ve formatla
        title = file_name.replace(".md", "").replace("-", " ").title()
        
        # SEO ve Google News için Dinamik Link Yapısı (Klasör adını blog/ yaptım, değiştirebilirsin)
        slug = file_name.replace(".md", "")
        post_url = f"{BASE_URL}/blog/{slug}"
        
        # Differ ve RSS botları için benzersiz (unique) GUID
        guid = f"sietra-post-{slug}"
        
        # Temiz ve kısa açıklama (Markdown etiketlerini veya HTML'i kabaca temizleyebilirsin gerekirse)
        # Şimdilik ilk 300 karakteri alıp üç nokta koyuyoruz
        description = content[:300].replace("\n", " ").strip()
        
        # ÇÖZÜM: Dosyanın gerçek sisteme taşınma/yazılma tarihini alıyoruz (Her seferinde değişmez)
        file_mtime = os.path.getmtime(file_path)
        pub_date = datetime.fromtimestamp(file_mtime).strftime("%a, %d %b %Y %H:%M:%S +0300")
        
        rss_items += f"""
        <item>
            <title><![CDATA[{title}]]></title>
            <link>{post_url}</link>
            <description><![CDATA[{description}...]]></description>
            <content:encoded><![CDATA[{content}]]></content:encoded>
            <pubDate>{pub_date}</pubDate>
            <guid isPermaLink="false">{guid}</guid>
            <dc:creator>Müslim SEVİNDİK</dc:creator>
        </item>"""

    rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" 
    xmlns:content="http://purl.org/rss/1.0/modules/content/"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
    <title>Sietra Elektrik Blog</title>
    <link>{BASE_URL}</link>
    <description>LED Aydınlatma ve Enerji Teknolojileri Uzmanlık Blogu</description>
    <language>tr</language>
    <atom:link href="{BASE_URL}/{FEED_FILE}" rel="self" type="application/rss+xml" />
    {rss_items}
</channel>
</rss>"""

    with open(FEED_FILE, "w", encoding="utf-8") as f:
        f.write(rss_content)

def run():
    if not os.path.exists(PUBLISHED_DIR): os.makedirs(PUBLISHED_DIR)
    if not os.path.exists(POSTS_DIR): return
        
    # Dosyaları isim sırasına göre al (Arşivin sırasını bozmaz)
    files = sorted([f for f in os.listdir(POSTS_DIR) if f.endswith('.md')])
    
    if not files:
        print("Arşivde yayınlanacak yeni yazı kalmadı!")
        return

    to_publish_now = files[:LIMIT]
    
    # Yeni dosyaları taşı
    for file_name in to_publish_now:
        os.rename(os.path.join(POSTS_DIR, file_name), os.path.join(PUBLISHED_DIR, file_name))
    
    # Son yayınlanan 10 yazıyı feed'de tut (Yeniden eskiye doğru sıralı)
    all_published = sorted([f for f in os.listdir(PUBLISHED_DIR) if f.endswith('.md')], reverse=True)
    recent_published = all_published[:10] 
    
    create_rss_feed(recent_published)
    print(f"Başarıyla {len(to_publish_now)} yazı yayınlandı ve feed güncellendi.")

if __name__ == "__main__":
    run()
