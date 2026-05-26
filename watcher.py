import os
import json
import yt_dlp

CHANNEL_URLS = {
    "Yannic Kilcher": "https://www.youtube.com/@YannicKilcher/videos",
    "Matthew Berman": "https://www.youtube.com/@MatthewBerman/videos"
}

def fetch_latest_videos():
    video_list = []
    
    # Updated options: removed flat extraction to ensure we get absolute core metadata
    ydl_opts = {
        'playlistend': 3,
        'quiet': True,
        'no_warnings': True,
        # Forces yt-dlp to request the true, static upload date property from the video object
        'force_generic_extractor': False
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for name, url in CHANNEL_URLS.items():
            print(f"Fetching precise video data for {name}...")
            try:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            # YouTube keeps the definitive absolute date string in 'upload_date' (YYYYMMDD)
                            raw_date = entry.get("upload_date")
                            if raw_date and len(raw_date) == 8:
                                formatted_date = f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
                            else:
                                formatted_date = "Unknown Date"
                            
                            video_list.append({
                                "channel": name,
                                "title": entry.get("title"),
                                "video_id": entry.get("id"),
                                "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                                "date": formatted_date
                            })
            except Exception as e:
                print(f"Error scraping precise dates for {name}: {e}")
    return video_list

def main():
    os.makedirs("data", exist_ok=True)
    videos = fetch_latest_videos()
    
    manifest = {"videos": videos}
    with open("data/manifest.json", "w") as f:
        json.dump(manifest, f, indent=4)
        
    print(f"\nSuccess! Saved {len(videos)} videos with absolute true upload dates to data/manifest.json")

if __name__ == "__main__":
    main()
