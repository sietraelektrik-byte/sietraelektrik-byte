import os
import re
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime

OUTPUT_DIR = "arsiv"
FEED_URL = "https://ledlamba.com/feed"
README_PATH = "README.md"

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
    """HTML içeriğini temizler, iç linkleri Markdown formatına çevirir"""
    if not html_content:
        return ""
    
    html_content = html_content.replace('https://ledlamba.com/feed/#', '#')
    html_content = html_content.replace('https://ledlamba.com/feed#', '#')
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    for element in soup.find_all(class_=[
        'toc', 'xs_social_share_widget', 'wslu-share-box-shaped', 
        'seo-tag', 'breadcrumbs', 'nav-links'
    ]):
        element.decompose()
        
    for header_tag in soup.find_all('header'):
        header_tag.decompose()

    for a in soup.find_all('a'):
        href = a.get('href', '').strip()
        text = a.get_text().strip()
        if href and text:
            a.replace_with(f"[{text}]({href})")
        elif text:
            a.replace_with(text)

    for strong in soup.find_all(['strong', 'b']):
        strong.replace_with(f" **{strong.get_text().strip()}** ")
    for em in soup.find_all(['em', 'i']):
        em.replace_with(f" *{em.get_text().strip()}* ")

    for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        level = int(h.name[1])
        h.replace_with(f"\n\n{'#' * level} {h.get_text().strip()}\n\n")
        
    for p in soup.find_all('p'):
        p.replace_with(f"\n{p.get_text().strip()}\n")
        
    for li in soup.find_all('li'):
        li.replace_with(f"* {li.get_text().strip()}\n")

    for table in soup.find_all('table'):
        markdown_table = []
        rows = table.find_all('tr')
        for i, row in enumerate(rows):
            cells = [cell.get_text().strip().replace('|', '\\|') for cell in row.find_all(['th', 'td'])]
            if not any(cells):
                continue
            markdown_table.append(f"| {' | '.join(cells)} |")
            if i == 0:
                markdown_table.append(f"| {' | '.join(['---'] * len(cells))} |")
        table.replace_with("\n\n" + "\n".join(markdown_table) + "\n\n")

    text_content = soup.get_text()
    text_content = re.sub(r'\[\s+', '[', text_content)
    text_content = re.sub(r'\s+\]', ']', text_content)
    text_content = re.sub(r'\n\s*\n', '\n\n', text_content)
    
    return text_content.strip()

def update_readme(latest_entries):
    """README.md dosyasındaki son 10 yazıyı otomatik günceller"""
    if not os.path.exists(README_PATH):
        print("README.md bulunamadı, işlem atlanıyor.")
        return

    with open(README_PATH, "r", encoding="utf-8") as f:
        readme_content = f.read()

    # Son yazıları tarih bazlı doğrulamak için listeyi sırala (En yeni en üstte)
    latest_entries.sort(key=lambda x: x.get('published_parsed', datetime.now().timetuple()), reverse=True)

    blog_list_md = "\n"
    for entry in latest_entries[:10]:
        title = entry['title']
        title_lower = title.lower()
        
        # Uluslararası içerikler için dil/bayrak/küre ikonu ataması
        if any(lang in title_lower for lang in ['أنظمة', 'прифатливи', 'достапни', 'доступні']):
            icon = "🌐"
        else:
            icon = "📝"
            
        archive_link = f"arsiv/{slugify(title)}.md"
        blog_list_md += f"- {icon} [{title}]({archive_link})\n"
    blog_list_md += "\n"

    # README içindeki START ve END etiketlerini bulup sadece o aralığı besle
    pattern = re.compile(r"(<!-- START_BLOG -->)(.*?)(<!-- END_BLOG -->)", re.DOTALL)
    
    if not pattern.search(readme_content):
        print("README.md içinde <!-- START_BLOG --> etiketleri bulunamadı!")
        return

    new_content = pattern.sub(f"\\1{blog_list_md}\\3", readme_content)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("README.md en güncel kronolojik 10 yazı ile başarıyla senkronize edildi!")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    page = 1
    processed_titles = set()
    all_entries = []

    while True:
        url = f"{FEED_URL}?paged={page}"
        print(f"Feed taranıyor: Sayfa {page}...")
        feed = feedparser.parse(url)
        
        if not feed.entries:
            break

        for entry in feed.entries:
            title = entry.title
            link = entry.link
            
            if title in processed_titles:
                continue
                
            # README takibi için gerekli verileri topla
            all_entries.append({
                'title': title, 
                'link': link, 
                'published_parsed': entry.get('published_parsed', None)
            })
            
            if 'content' in entry:
                raw_content = entry.content[0].value
            elif 'summary' in entry:
                raw_content = entry.summary
            else:
                raw_content = ""

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
            
            processed_titles.add(title)
            
        page += 1

    # Tüm feed başarıyla taranıp arşivlendikten sonra ana sayfa README'yi tetikle
    if all_entries:
        update_readme(all_entries)

if __name__ == "__main__":
    main()
