import os
import requests
from bs4 import BeautifulSoup
import yt_dlp

# پوشه‌های ورودی و خروجی
LINKS_DIR = "links"
VIDEOS_DIR = "videos"

# ایجاد پوشه‌ها در صورت عدم وجود
os.makedirs(LINKS_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

def extract_video_links(url):
    """استخراج لینک‌های ویدیویی از یک صفحه"""
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ خطا در دریافت صفحه {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    video_links = []

    # پیدا کردن لینک‌های ویدیویی (مثلاً mp4، m3u8 و یوتیوب)
    for tag in soup.find_all(["source", "iframe", "a"]):
        src = tag.get("src") or tag.get("href")
        if src and ("mp4" in src or "youtube.com" in src or "youtu.be" in src or "m3u8" in src):
            video_links.append(src)

    return video_links

def download_video(url):
    """دانلود ویدیو از لینک"""
    ydl_opts = {
        'outtmpl': os.path.join(VIDEOS_DIR, '%(title)s.%(ext)s'),
        'format': 'best',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            print(f"📥 در حال دانلود: {url}")
            ydl.download([url])
        except Exception as e:
            print(f"❌ دانلود ناموفق {url}: {e}")

def process_links():
    """بررسی فایل‌های لینک‌ها و دانلود ویدیوها"""
    for filename in os.listdir(LINKS_DIR):
        if filename.endswith(".txt"):
            filepath = os.path.join(LINKS_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                links = [line.strip() for line in f.readlines() if line.strip()]

            for link in links:
                print(f"🔍 بررسی: {link}")
                video_links = extract_video_links(link)
                
                if not video_links:
                    print(f"❌ ویدیویی پیدا نشد در {link}")
                else:
                    for video in video_links:
                        download_video(video)

if __name__ == "__main__":
    process_links()
