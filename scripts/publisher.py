import os
from datetime import datetime
import html

# Yapılandırma
POSTS_DIR = "blog-archive"
PUBLISHED_DIR = "published_posts"
FEED_FILE = "feed.xml"
LIMIT = 2

def create_rss_feed(published_files):
    rss_items = ""
    for file_name in published_files:
        file_path = os.path.join(PUBLISHED_DIR, file_name)
        
        # Makale içeriğini oku
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Markdown içeriğini HTML uyumlu hale getir (basit kaçış)
            safe_content = html.escape(content)

        title = file_name.replace(".md", "").replace("-", " ").title()
        link = f"https://github.com/sietraelektrik-byte/sietraelektrik-byte/tree/main/{PUBLISHED_DIR}/{file_name}"
        pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0300")
        
        rss_items += f"""
        <item>
            <title>{title}</title>
            <link>{link}</link>
            <description>{safe_content}</description>
            <pubDate>{pub_date}</pubDate>
            <guid>{link}</guid>
        </item>"""

    rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
    <title>Sietra Elektrik Blog</title>
    <link>https://ledlamba.com</link>
    <description>LED Aydınlatma ve Enerji Teknolojileri Uzmanlık Blogu</description>
    {rss_items}
</channel>
</rss>"""

    with open(FEED_FILE, "w", encoding="utf-8") as f:
        f.write(rss_content)

def run():
    if not os.path.exists(PUBLISHED_DIR): os.makedirs(PUBLISHED_DIR)
    if not os.path.exists(POSTS_DIR): return
        
    files = sorted([f for f in os.listdir(POSTS_DIR) if f.endswith('.md')])
    to_publish = files[:LIMIT]
    
    for file_name in to_publish:
        os.rename(os.path.join(POSTS_DIR, file_name), os.path.join(PUBLISHED_DIR, file_name))
    
    all_published = [f for f in os.listdir(PUBLISHED_DIR) if f.endswith('.md')]
    create_rss_feed(all_published)

if __name__ == "__main__":
    run()
