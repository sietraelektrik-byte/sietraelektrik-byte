import feedparser
import os
import re

# Sitenin RSS adresi
RSS_URL = "https://ledlamba.com/feed"
feed = feedparser.parse(RSS_URL)

# Arşiv klasörü yolu
ARCHIVE_DIR = "blog-archive"

if not os.path.exists(ARCHIVE_DIR):
    os.makedirs(ARCHIVE_DIR)

for entry in feed.entries:
    # Başlığı dosya adına çevir (Türkçe karakter ve boşluk düzenlemesi)
    clean_title = re.sub(r'[^\w\s-]', '', entry.title).strip().lower()
    clean_title = re.sub(r'[-\s]+', '-', clean_title)
    file_path = os.path.join(ARCHIVE_DIR, f"{clean_title}.md")

    # Eğer bu yazı daha önce arşivlenmediyse oluştur
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {entry.title}\n\n")
            f.write(f"**Tarih:** {entry.published}\n\n")
            f.write(f"{entry.summary[:400]}...\n\n")
            f.write(f"---\n")
            f.write(f"**Makalenin Tamamı:** [{entry.link}]({entry.link})\n\n")
            f.write(f"*Bu içerik Sietra Elektrik teknik arşivi için otomatik oluşturulmuştur.*")
        print(f"Yeni yazı arşivlendi: {entry.title}")
