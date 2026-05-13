import os
import requests

# Yapılandırma
POSTS_DIR = "blog-archive" 
PUBLISHED_DIR = "published_posts"
API_URL = "https://api.differ.blog/v1/posts" 
LIMIT = 3 

def extract_keywords(content):
    tech_keywords = ["LED", "DALI", "D4i", "IoT", "Smart Lighting", "Energy", "Solar", "Tekirdağ", "GÖZYUMMAZ"]
    found = [word for word in tech_keywords if word.lower() in content.lower()]
    return found[:5]

def publish_posts():
    if not os.path.exists(PUBLISHED_DIR): os.makedirs(PUBLISHED_DIR)
    files = sorted([f for f in os.listdir(POSTS_DIR) if f.endswith('.md')])
    to_publish = files[:LIMIT]

    for file_name in to_publish:
        file_path = os.path.join(POSTS_DIR, file_name)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        keywords = extract_keywords(content)
        payload = {
            "title": file_name.replace(".md", "").replace("-", " ").title(),
            "body": content + f"\n\n---\n*Kaynak: [ledlamba.com](https://ledlamba.com)*",
            "tags": keywords,
            "status": "public",
            "publish_immediately": True
        }
        headers = {"Authorization": f"Bearer {os.getenv('PLATFORM_API_KEY')}", "Content-Type": "application/json"}
        
        response = requests.post(API_URL, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            os.rename(file_path, os.path.join(PUBLISHED_DIR, file_name))
            print(f"🚀 {file_name} yayınlandı!")

if __name__ == "__main__":
    publish_posts()

