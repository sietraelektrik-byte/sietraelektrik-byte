import os
from datetime import datetime
import re

# Yapılandırma
POSTS_DIR = "blog-archive"
PUBLISHED_DIR = "published_posts"
FEED_FILE = "feed.xml"
README_FILE = "README.md"
# 63 yazının tamamını tek seferde yayına almak ve feed'e basmak için limiti kaldırdık veya büyük bir sayı yaptık
LIMIT = 500 
BASE_URL = "https://ledlamba.com"

def create_rss_feed(recent_files):
    """Differ ve Dev.to standartlarına %100 uyumlu bulk feed üretici"""
    rss_items = ""
    for file_name in recent_files:
        file_path = os.path.join(PUBLISHED_DIR, file_name)
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Orijinal dosya adından başlık türetme mantığın
        title = file_name.replace(".md", "").replace("-", " ").title()
        slug = file_name.replace(".md", "")
        post_url = f"{BASE_URL}/{slug}" # Sitenizdeki orijinal link yapısı
        guid = f"sietra-post-{slug}"
        
        # Bulk platformların hata vermemesi için temiz açıklama
        clean_desc = re.sub(r'<[^<]+?>', '', content)
        clean_desc = re.sub(r'[#*`\-\[\]]', '', clean_desc)
        description = clean_desc[:300].replace("\n", " ").strip()
        
        # Sabit Tarih: Dosyanın gerçek sisteme işlenme zamanı
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

def update_readme(recent_files):
    """README.md içindeki anchor linkleri sitene çıkacak şekilde eksiksiz onarır"""
    if not os.path.exists(README_FILE):
        return

    with open(README_FILE, "r", encoding="utf-8") as f:
        readme_content = f.read()

    header_marker = "✍️ Son Blog Yazılarım"
    if header_marker not in readme_content:
        return

    top_part = readme_content.split(header_marker)[0] + header_marker + "\n\n"
    
    # Profilinde tam olarak son 10 yazıyı sitene giden orijinal anchor linklerle basıyoruz
    blog_links = ""
    for file_name in recent_files[:10]:
        title = file_name.replace(".md", "").replace("-", " ").title()
        slug = file_name.replace(".md", "")
        post_url = f"{BASE_URL}/{slug}"
        # Senin istediğin gerçek anchor link formatı:
        blog_links += f"[{title}]({post_url})\n\n"

    # Alt kısımda kalan repo açıklama alanını koruyoruz
    footer_marker = "sietraelektrik-byte/sietraelektrik-byte"
    bottom_part = ""
    if footer_marker in readme_content:
        bottom_part = "\n" + footer_marker + readme_content.split(footer_marker)[1]
    else:
        bottom_part = "\n\n_sietraelektrik-byte/sietraelektrik-byte is a special repository._"

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(top_part + blog_links + bottom_part)

def run():
    if not os.path.exists(PUBLISHED_DIR): os.makedirs(PUBLISHED_DIR)
    if not os.path.exists(POSTS_DIR): return
        
    # Arşivdeki tüm dosyaları oku
    files = sorted([f for f in os.listdir(POSTS_DIR) if f.endswith('.md')])
    
    if files:
        # LIMIT = 100 yaptığımız için 63 yazının tamamını tek seferde published_posts'a taşır
        to_publish_now = files[:LIMIT]
        for file_name in to_publish_now:
            os.rename(os.path.join(POSTS_DIR, file_name), os.path.join(PUBLISHED_DIR, file_name))
        print(f"{len(to_publish_now)} yazının tamamı arşive başarıyla taşındı.")
    
    # published_posts klasöründeki her şeyi yeniden eskiye sırala
    all_published = sorted([f for f in os.listdir(PUBLISHED_DIR) if f.endswith('.md')], reverse=True)
    
    # Feed içinde tüm yazıların (63 tane) görünmesi için feed beslemesini sınırlamıyoruz
    if all_published:
        create_rss_feed(all_published)
        # Profilinde ise sadece en güncel son 10 yazıyı gösteriyoruz
        update_readme(all_published)
        print("feed.xml (Tüm yazılar) ve README.md (Son 10 link) başarıyla güncellendi.")

if __name__ == "__main__":
    run()
