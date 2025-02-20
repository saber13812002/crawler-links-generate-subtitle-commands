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

def extract_direct_mp4_links(url):
    """استخراج لینک‌های مستقیم mp4 از صفحه"""
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # پیدا کردن تگ‌های ویدیو
        video_tags = soup.find_all("video")
        mp4_links = []
        
        for video in video_tags:
            # بررسی ویژگی src
            src = video.get("src")
            if src and src.endswith(".mp4"):
                mp4_links.append(src)
                
            # بررسی تگ‌های source داخل ویدیو
            sources = video.find_all("source")
            for source in sources:
                src = source.get("src")
                if src and src.endswith(".mp4"):
                    mp4_links.append(src)
                    
        return mp4_links
        
    except requests.exceptions.RequestException as e:
        print(f"❌ خطا در دریافت صفحه {url}: {e}")
        return []

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
            base_name = os.path.splitext(filename)[0]
            done_file = os.path.join(LINKS_DIR, f"{base_name}.done")
            
            # بررسی فایل done برای جلوگیری از دانلود مجدد
            processed_links = set()
            if os.path.exists(done_file):
                with open(done_file, "r", encoding="utf-8") as f:
                    processed_links = set(line.strip() for line in f)

            filepath = os.path.join(LINKS_DIR, filename)
            video_output_dir = os.path.join(VIDEOS_DIR, base_name)
            os.makedirs(video_output_dir, exist_ok=True)

            with open(filepath, "r", encoding="utf-8") as f:
                links = [line.strip() for line in f.readlines() if line.strip()]

            new_processed_links = set()
            for link in links:
                if link in processed_links:
                    print(f"⏭️ لینک قبلاً دانلود شده: {link}")
                    continue

                print(f"🔍 بررسی: {link}")
                video_links = extract_direct_mp4_links(link)
                
                if not video_links:
                    # بررسی برای تگ video در HTML
                    response = requests.get(link, headers={"User-Agent": "Mozilla/5.0"})
                    soup = BeautifulSoup(response.text, "html.parser")
                    video_tags = soup.find_all("video")
                    for video in video_tags:
                        src = video.get("src")
                        if src:
                            video_links.append(src)

                if not video_links:
                    print(f"❌ ویدیویی پیدا نشد در {link}")
                else:
                    for video in video_links:
                        ydl_opts = {
                            'outtmpl': os.path.join(video_output_dir, '%(title)s.%(ext)s'),
                            'format': 'best',
                        }
                        download_video(video)
                    new_processed_links.add(link)

            # ذخیره لینک‌های پردازش شده در فایل done
            if new_processed_links:
                with open(done_file, "a", encoding="utf-8") as f:
                    for link in new_processed_links:
                        f.write(f"{link}\n")
                
            # تولید دستور برای ابزار تحلیل محتوا
            print(f"\n🤖 دستور تحلیل محتوا:")
            print(f'python content_analyzer.py --directory "{video_output_dir}"')

if __name__ == "__main__":
    process_links()
