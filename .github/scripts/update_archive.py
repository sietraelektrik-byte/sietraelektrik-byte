import os
import re
import feedparser
from bs4 import BeautifulSoup

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

def clean_and_convert_html(html_content):
    """HTML içeriğini temizler, linkleri korur ve saf Markdown'a çevirir"""
    if not html_content:
        return ""
    
    # 1. Hatalı feed link yapısını anında düzelt
    html_content = html_content.replace('https://ledlamba.com/feed/#', '#')
    html_content = html_content.replace('https://ledlamba.com/feed#', '#')
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 2. Çöp ve kalabalık yapan alanları kökten temizle
    for element in soup.find_all(class_=[
        'toc', 'xs_social_share_widget', 'wslu-share-box-shaped', 
        'seo-tag', 'breadcrumbs', 'nav-links'
    ]):
        element.decompose()
        
    for header_tag in soup.find_all('header'):
        header_tag.decompose()

    # 3. HTML elemanlarını temiz Markdown yapılarına dönüştür
    for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        level = int(h.name[1])
        h.replace_with(f"\n\n{'#' * level} {h.get_text().strip()}\n\n")
        
    for p in soup.find_all('p'):
        p.replace_with(f"\n{p.get_text().strip()}\n")
        
    for li in soup.find_all('li'):
        # İçindeki linkleri bozmamak için text yerine doğrudan eleman kontrolü yapabiliriz
        li.replace_with(f"* {li.get_text().strip()}\n")

    # 4. Tabloları düzgün okunabilir Markdown tablosuna çevir
    for table in soup.find_all('table'):
        markdown_table = []
        rows = table.find_all('tr')
        for i, row in enumerate(rows):
            cells = [cell.get_text().strip().replace('|', '\\|') for cell in row.find_all(['th', 'td'])]
            markdown_table.append(f"| {' | '.join(cells)} |")
            if i == 0:  # Header altı çizgisi
                markdown_table.append(f"| {' | '.join(['---'] * len(cells))} |")
        table.replace_with("\n\n" + "\n".join(markdown_table) + "\n\n")

    # Temizlenmiş metni al ve çoklu boşlukları düzenle
    text_content = soup.get_text()
    text_content = re.sub(r'\n\s*\n', '\n\n', text_content)
    
    return text_content.strip()

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    page = 1
    processed_titles = set()

    while True:
        url = f"{FEED_URL}?paged={page}"
        print(f"Feed taranıyor: Sayfa {page}...")
        feed = feedparser.parse(url)
        
        if not feed.entries:
            print(f"Tarama tamamlandı. Tüm sayfalar işlendi.")
            break

        for entry in feed.entries:
            title = entry.title
            link = entry.link
            
            if title in processed_titles:
                continue
                
            if 'content' in entry:
                raw_content = entry.content[0].value
            elif 'summary' in entry:
                raw_content = entry.summary
            else:
                raw_content = ""

            # HTML'den arındırılmış kusursuz Markdown içeriği
            content = clean_and_convert_html(raw_content)

            filename = f"{slugify(title)}.md"
            filepath = os.path.join(OUTPUT_DIR, filename)

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
            print(f"Jilet gibi arşive eklendi: {filename}")
            processed_titles.add(title)
            
        page += 1

if __name__ == "__main__":
    main()
