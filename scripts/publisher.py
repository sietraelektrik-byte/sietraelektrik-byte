import os
from datetime import datetime

# Yapılandırma
POSTS_DIR = "blog-archive"
PUBLISHED_DIR = "published_posts"
FEED_FILE = "feed.xml"
LIMIT = 3

def create_rss_feed(published_files):
    rss_items = ""
    for file_name in published_files:
        title = file_name.replace(".md", "").replace("-", " ").title()
        link = f"https://github.com/sietraelektrik-byte/sietraelektrik-byte/tree/main/{PUBLISHED_DIR}/{file_name}"
        pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0300")
        
        rss_items += f"""
        <item>
            <title>{title}</title>
            <link>{link}</link>
            <description>Sietra Elektrik Teknik Makalesi: {title}</description>
            <pubDate>{pub_date}</pubDate>
        </item>"""

    rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
    <title>Sietra Elektrik Blog</title>
    <link>https://ledlamba.com</link>
    <description>LED Aydınlatma ve Enerji Teknolojileri</description>
    {rss_items}
</channel>
</rss>"""

    with open(FEED_FILE, "w", encoding="utf-8") as f:
        f.write(rss_content)

def run():
    # Klasörleri kontrol et ve oluştur
    if not os.path.exists(PUBLISHED_DIR): os.makedirs(PUBLISHED_DIR)
    
    # Arşivdeki .md dosyalarını al
    if not os.path.exists(POSTS_DIR):
        print(f"Hata: {POSTS_DIR} klasörü bulunamadı!")
        return
        
    files = sorted([f for f in os.listdir(POSTS_DIR) if f.endswith('.md')])
    to_publish = files[:LIMIT]
    
    if not to_publish:
        print("Yayınlanacak yeni yazı yok.")
        return

    # Dosyaları taşı
    for file_name in to_publish:
        os.rename(os.path.join(POSTS_DIR, file_name), os.path.join(PUBLISHED_DIR, file_name))
    
    # Tüm yayınlanmış dosyaları RSS'e ekle
    all_published = [f for f in os.listdir(PUBLISHED_DIR) if f.endswith('.md')]
    create_rss_feed(all_published)
    print(f"🚀 {len(to_publish)} yazı taşındı ve {FEED_FILE} güncellendi!")

if __name__ == "__main__":
    run()

