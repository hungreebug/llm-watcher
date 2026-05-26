import os
import json
import yt_dlp

CHANNEL_URLS = {
    "Andrej Karpathy": "https://www.youtube.com/@AndrejKarpathy/videos",
    "Matt Wolfe": "https://www.youtube.com/@mreflow/videos",
    "Wes Roth": "https://www.youtube.com/@WesRoth/videos",
    "Lex Fridman": "https://www.youtube.com/@lexfridman/videos",
    "Two Minute Papers": "https://www.youtube.com/@TwoMinutePapers/videos",
    "Matthew Berman": "https://www.youtube.com/@matthew_berman/videos",
    "StatQuest": "https://www.youtube.com/@statquest/videos"
}

def fetch_latest_videos():
    video_list = []
    ydl_opts = {
        'playlistend': 2, # Skims the 2 most recent videos per channel to manage your data scope elegantly
        'quiet': True,
        'no_warnings': True,
        'force_generic_extractor': False
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for name, url in CHANNEL_URLS.items():
            print(f"Fetching precise upload dates for {name}...")
            try:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            raw_date = entry.get("upload_date")
                            if raw_date and len(raw_date) == 8:
                                formatted_date = f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
                            else:
                                formatted_date = "Recent"
                            
                            video_list.append({
                                "channel": name,
                                "title": entry.get("title"),
                                "video_id": entry.get("id"),
                                "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                                "date": formatted_date
                            })
            except Exception as e:
                print(f"Could not scan feed for {name}: {e}")
    return video_list

def main():
    os.makedirs("data", exist_ok=True)
    videos = fetch_latest_videos()
    
    manifest = {"videos": videos}
    with open("data/manifest.json", "w") as f:
        json.dump(manifest, f, indent=4)
        
    print(f"\nSuccess! Cataloged {len(videos)} new channel targets with exact true upload dates.")

if __name__ == "__main__":
    main()
