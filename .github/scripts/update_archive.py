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
    """HTML içeriğini temizler, iç linkleri Markdown formatına ([Metin](URL)) çevirir"""
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

    # 3. ÖNEMLİ: Linkleri (<a>) düz metne düşürmeden Markdown formatına çevir
    for a in soup.find_all('a'):
        href = a.get('href', '').strip()
        text = a.get_text().strip()
        if href and text:
            # Eğer dahili sayfa içi link değilse ve başında http yoksa tamamla
            a.replace_with(f"[{text}]({href})")
        elif text:
            a.replace_with(text)

    # 4. Kalın ve Eğik Yazıları Markdown'a Çevir
    for strong in soup.find_all(['strong', 'b']):
        strong.replace_with(f" **{strong.get_text().strip()}** ")
    for em in soup.find_all(['em', 'i']):
        em.replace_with(f" *{em.get_text().strip()}* ")

    # 5. Başlıkları Markdown'a Çevir
    for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        level = int(h.name[1])
        h.replace_with(f"\n\n{'#' * level} {h.get_text().strip()}\n\n")
        
    # 6. Listeleri ve Paragrafları Düzenle
    for p in soup.find_all('p'):
        p.replace_with(f"\n{p.get_text().strip()}\n")
        
    for li in soup.find_all('li'):
        li.replace_with(f"* {li.get_text().strip()}\n")

    # 7. Tabloları düzgün okunabilir Markdown tablosuna çevir
    for table in soup.find_all('table'):
        markdown_table = []
        rows = table.find_all('tr')
        for i, row in enumerate(rows):
            cells = [cell.get_text().strip().replace('|', '\\|') for cell in row.find_all(['th', 'td'])]
            # Eğer boş satır denk gelirse atla
            if not any(cells):
                continue
            markdown_table.append(f"| {' | '.join(cells)} |")
            if i == 0:  # Header altı çizgisi
                markdown_table.append(f"| {' | '.join(['---'] * len(cells))} |")
        table.replace_with("\n\n" + "\n".join(markdown_table) + "\n\n")

    # Son temizlik: HTML kalıntılarını temizle ve çoklu boşlukları düzenle
    text_content = soup.get_text()
    
    # Markdown link yapay boşluklarını temizle (örn: "[ Metin ]( URL )" -> "[Metin](URL)")
    text_content = re.sub(r'\[\s+', '[', text_content)
    text_content = re.sub(r'\s+\]', ']', text_content)
    
    # Satır boşluklarını jilet gibi yap
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

            # HTML'den arındırılmış, linkleri korunmuş mükemmel Markdown
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
            print(f"Linkleri ile birlikte arşive eklendi: {filename}")
            processed_titles.add(title)
            
        page += 1

if __name__ == "__main__":
    main()
