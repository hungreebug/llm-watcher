import os
import json
import time
from google import genai
from youtube_transcript_api import YouTubeTranscriptApi

client = genai.Client()

def get_video_transcript(video_id):
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.fetch(video_id, languages=['en'])
        text = " ".join([item.text for item in transcript_list])
        return text
    except Exception as e:
        print(f"   Could not download transcript for {video_id}: {e}")
        return None

def analyze_transcript_with_gemini(title, transcript_text):
    prompt = f"""
    You are an AI research assistant. Analyze this transcript for a video titled "{title}".
    Provide a concise 2-sentence summary of the core message or breakthrough mentioned.
    Then, provide an array of relevant domain tags (e.g., "AI Safety", "LLMs", "Governance", "Agents", "Cocktails").
    
    Respond STRICTLY in the following raw JSON format:
    {{
        "summary": "Your 2-sentence summary here.",
        "tags": ["Tag1", "Tag2", "Tag3"]
    }}
    
    Transcript text snippet:
    {transcript_text[:6000]}
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"   Gemini analysis failed: {e}")
        return None

def generate_macro_insights(all_videos_data):
    """Asks Gemini to analyze how the channels relate to each other on LLM themes"""
    prompt = f"""
    You are a strategic AI research analyst. Look at this collection of video summaries and metadata from different creators:
    {json.dumps(all_videos_data, indent=2)}
    
    Analyze how these channels relate to each other on LLM themes and core topics.
    Provide a concise synthesis addressing:
    1. The core content focus of each creator.
    2. How they complement or diverge from each other on LLM themes.
    
    Respond STRICTLY in the following raw JSON format:
    {{
        "relationship_synthesis": "Your concise analysis paragraph here detailing the cross-channel relationships on LLM themes."
    }}
    """
    try:
        print("\n🧠 Asking Gemini to generate cross-channel relationship insights...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        return json.loads(response.text).get("relationship_synthesis")
    except Exception as e:
        print(f"   Macro insights generation skipped or failed: {e}")
        return "Cross-channel thematic relationship synthesis is currently processing."

def main():
    if not os.path.exists("data/manifest.json"):
        print("Error: data/manifest.json missing. Run watcher.py first.")
        return
        
    with open("data/manifest.json", "r") as f:
        manifest = json.load(f)
        
    cache = {}
    if os.path.exists("data/table.json"):
        try:
            with open("data/table.json", "r") as f:
                old_data = json.load(f)
                for v in old_data.get("processed_videos", []):
                    if "RESOURCE_EXHAUSTED" not in v.get("summary", "") and v.get("tags") != ["Error"]:
                        cache[v["url"]] = v
        except Exception:
            pass

    table_data = []
    
    for video in manifest["videos"]:
        print(f"\nProcessing: {video['title']}...")
        
        if video["url"] in cache:
            print("   ✅ Found in cache! Skipping Gemini API call.")
            # Preserve or append the date field from the manifest into the cached row
            cached_row = cache[video["url"]]
            cached_row["date"] = video.get("date", "Recent")
            table_data.append(cached_row)
            continue
            
        transcript = get_video_transcript(video["video_id"])
        
        if transcript:
            print("   Transcript fetched successfully! Asking Gemini to analyze...")
            analysis = analyze_transcript_with_gemini(video["title"], transcript)
            
            if analysis:
                video_entry = {
                    "channel": video["channel"],
                    "title": video["title"],
                    "url": video["url"],
                    "date": video.get("date", "Recent"),
                    "summary": analysis.get("summary"),
                    "tags": analysis.get("tags")
                }
            else:
                video_entry = {
                    "channel": video["channel"],
                    "title": video["title"],
                    "url": video["url"],
                    "date": video.get("date", "Recent"),
                    "summary": "Gemini analysis failed (Quota block). Will retry on next run.",
                    "tags": ["Error"]
                }
            table_data.append(video_entry)
            print("   Pacing pause... waiting 5 seconds before the next call.")
            time.sleep(5)
        else:
            video_entry = {
                "channel": video["channel"],
                "title": video["title"],
                "url": video["url"],
                "date": video.get("date", "Recent"),
                "summary": "No English captions or transcript available for this video upload.",
                "tags": ["No Transcript"]
            }
            table_data.append(video_entry)
            
    # --- MACRO INSIGHTS GENERATION LAYER ---
    macro_synthesis = generate_macro_insights(table_data)
            
    # Save everything into a single master payload file for our frontend
    final_output = {
        "channel_relationships": macro_synthesis,
        "processed_videos": table_data
    }
    
    with open("data/table.json", "w") as f:
        json.dump(final_output, f, indent=4)
        
    print("\n🚀 Step 1 Backend Complete! Data saved to data/table.json")

if __name__ == "__main__":
    main()
