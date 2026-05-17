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
        'â': 'a', 'î': 'i', 'û': 'u', 'I': 'i', 'İ': 'i'
    }
    for k, v in mapping.items():
        text = text.replace(k, v)
    text = re.sub(re.compile(r'[^\w\s-]'), '', text)
    return re.sub(re.compile(r'[-\s]+'), '-', text).strip('-')

def clean_content(html_content):
    """HTML içeriğindeki kırık feed yönlendirmelerini temizler ve dofollow linkleri korur"""
    if not html_content:
        return ""
    
    # 1. WordPress'in İçindekiler linklerindeki hatalı '/feed/#' kısımlarını doğrudan '#' yapar
    html_content = html_content.replace('https://ledlamba.com/feed/#', '#')
    html_content = html_content.replace('https://ledlamba.com/feed#', '#')
    
    # 2. Gereksiz sosyal medya widget kodlarını ve kalıntıları temizler
    html_content = re.sub(r'<div class="xs_social_share_widget.*?</div>', '', html_content, flags=re.DOTALL)
    
    return html_content

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    page = 1
    processed_titles = set()

    while True:
        # Sayfa sayfa tüm geçmişi tarıyoruz (?paged=1, ?paged=2...)
        url = f"{FEED_URL}?paged={page}"
        print(f"Feed taranıyor: Sayfa {page}...")
        feed = feedparser.parse(url)
        
        # Eğer sayfa boşsa veya içerik yoksa döngü biter (Tüm arşiv çekilmiş olur)
        if not feed.entries:
            print(f"Sayfa {page} boş veya artık yazı yok. Tarama başarıyla bitti.")
            break

        for entry in feed.entries:
            title = entry.title
            link = entry.link
            
            # Mükerrer işlemeyi engelle
            if title in processed_titles:
                continue
                
            if 'content' in entry:
                raw_content = entry.content[0].value
            elif 'summary' in entry:
                raw_content = entry.summary
            else:
                raw_content = ""

            # İçeriği dofollow yapısını bozmadan temizle
            content = clean_content(raw_content)

            filename = f"{slugify(title)}.md"
            filepath = os.path.join(OUTPUT_DIR, filename)

            # Markdown formatı ve SEO için Canonical etiketi
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
            print(f"Arşive Eklendi: {filename}")
            processed_titles.add(title)
            
        page += 1 # Sonraki arama sayfasına geç

if __name__ == "__main__":
    main()
