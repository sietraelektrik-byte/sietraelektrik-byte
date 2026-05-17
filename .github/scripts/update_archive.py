import os
import re
import feedparser

OUTPUT_DIR = "arsiv"
FEED_URL = "https://ledlamba.com/feed"

def slugify(text):
    """Dosya adları için başlığı temizler ve URL formatına getirir"""
    text = text.lower()
    mapping = {
        'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
        'â': 'a', 'î': 'i', 'û': 'u'
    }
    for k, v in mapping.items():
        text = text.replace(k, v)
    text = re.sub(re.compile(r'[^\w\s-]'), '', text)
    return re.sub(re.compile(r'[-\s]+'), '-', text).strip('-')

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print("Feed taranıyor...")
    feed = feedparser.parse(FEED_URL)
    
    if not feed.entries:
        print("Feed boş veya alınamadı!")
        return

    for entry in feed.entries:
        title = entry.title
        link = entry.link
        
        # İçeriği ham HTML olarak alıyoruz (Linkler ve dofollow yapısı bozulmaz)
        if 'content' in entry:
            content = entry.content[0].value
        elif 'summary' in entry:
            content = entry.summary
        else:
            content = ""

        filename = f"{slugify(title)}.md"
        filepath = os.path.join(OUTPUT_DIR, filename)

        # Markdown formatı ve en tepede Canonical etiketi
        md_content = f"""---
title: "{title}"
link: "{link}"
canonical: "{link}"
---

# {title}

{content}
"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"Kaydedildi: {filename}")

if __name__ == "__main__":
    main()

