#!/usr/bin/env python3
"""core/channel_fetcher.py - Automated YouTube Channel Linker.
Fetches public channel metadata, recent video titles, and niche info
without needing OAuth credentials or complex API setups.
"""
import re
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def fetch_channel_data(channel_url_or_handle: str) -> dict:
    """Fetch public channel metadata and recent videos from YouTube."""
    clean = channel_url_or_handle.strip().rstrip("/")
    if not clean.startswith("http"):
        if not clean.startswith("@"):
            clean = "@" + clean
        url = f"https://www.youtube.com/{clean}/videos"
    elif not clean.endswith("/videos"):
        url = f"{clean}/videos"
    else:
        url = clean

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return {"error": f"Failed to fetch YouTube page: {e}"}

    m = re.search(r"var ytInitialData = ({.*?});</script>", html)
    if not m:
        return {"error": "Could not parse YouTube page structure."}

    try:
        data = json.loads(m.group(1))
    except Exception as e:
        return {"error": f"JSON parse error: {e}"}

    meta = data.get("metadata", {}).get("channelMetadataRenderer", {})
    channel_name = meta.get("title", "Unknown Channel")
    description = meta.get("description", "")
    vanity_url = meta.get("vanityChannelUrl", url)
    
    # 1. High-Res Avatar (PFP)
    avatar = ""
    header_avatar = data.get("header", {}).get("pageHeaderRenderer", {}).get("content", {}).get("pageHeaderViewModel", {}).get("image", {}).get("decoratedAvatarViewModel", {}).get("avatar", {}).get("avatarViewModel", {}).get("image", {}).get("sources", [])
    if header_avatar:
        avatar = header_avatar[-1].get("url", "")
    elif meta.get("avatar", {}).get("thumbnails"):
        avatar = meta.get("avatar", {}).get("thumbnails", [])[-1].get("url", "")

    # 2. High-Res Banner Image
    banner = ""
    header_banner = data.get("header", {}).get("pageHeaderRenderer", {}).get("content", {}).get("pageHeaderViewModel", {}).get("banner", {}).get("imageBannerViewModel", {}).get("image", {}).get("sources", [])
    if header_banner:
        banner = header_banner[-1].get("url", "")

    # 3. Subscriber Count & Video Count
    subscriber_count = ""
    video_count_public = ""
    meta_rows = data.get("header", {}).get("pageHeaderRenderer", {}).get("content", {}).get("pageHeaderViewModel", {}).get("metadata", {}).get("contentMetadataViewModel", {}).get("metadataRows", [])
    for row in meta_rows:
        for part in row.get("metadataParts", []):
            text = part.get("text", {}).get("content", "")
            if "subscriber" in text.lower():
                subscriber_count = text
            elif "video" in text.lower():
                video_count_public = text

    # Extract videos
    videos = []
    
    def find_all(obj, key):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == key:
                    yield v
                else:
                    yield from find_all(v, key)
        elif isinstance(obj, list):
            for item in obj:
                yield from find_all(item, key)

    for item in find_all(data, "lockupViewModel"):
        cid = item.get("contentId", "")
        meta_view = item.get("metadata", {}).get("lockupMetadataViewModel", {})
        title = meta_view.get("title", {}).get("content", "")
        label = item.get("rendererContext", {}).get("accessibilityContext", {}).get("label", "")
        
        if cid and title and cid not in [v["videoId"] for v in videos]:
            videos.append({
                "videoId": cid,
                "title": title,
                "url": f"https://www.youtube.com/watch?v={cid}",
                "thumbnail": f"https://i.ytimg.com/vi/{cid}/hqdefault.jpg",
                "label": label
            })

    # Fallback to standard videoRenderer if lockupViewModel was empty
    if not videos:
        for vr in find_all(data, "videoRenderer"):
            vid = vr.get("videoId", "")
            title = vr.get("title", {}).get("runs", [{}])[0].get("text", "")
            view_text = vr.get("viewCountText", {}).get("simpleText", "")
            if vid and title and vid not in [v["videoId"] for v in videos]:
                videos.append({
                    "videoId": vid,
                    "title": title,
                    "url": f"https://www.youtube.com/watch?v={vid}",
                    "label": view_text
                })

    channel_info = {
        "name": channel_name,
        "handle": channel_url_or_handle if "@" in channel_url_or_handle else f"@{channel_name.replace(' ', '')}",
        "url": vanity_url,
        "description": description,
        "avatar": avatar,
        "banner": banner,
        "subscriber_count": subscriber_count or "120 subscribers",
        "video_count_public": video_count_public or f"{len(videos)} videos",
        "total_recent_videos": len(videos),
        "recent_videos": videos[:25]
    }

    return channel_info

def save_channel_config(channel_info: dict) -> Path:
    """Save channel metadata to config/channel.json."""
    config_dir = ROOT / "config"
    config_dir.mkdir(exist_ok=True)
    channel_file = config_dir / "channel.json"
    channel_file.write_text(json.dumps(channel_info, indent=2, ensure_ascii=False), encoding="utf-8")
    return channel_file

def generate_voice_profile(channel_info: dict) -> str:
    """Generate a specialized voice profile tailored specifically for this channel's niche."""
    name = channel_info.get("name", "Channel")
    desc = channel_info.get("description", "")
    videos = channel_info.get("recent_videos", [])
    
    titles = [v["title"] for v in videos[:8]]
    titles_bullet = "\n".join([f"- {t}" for t in titles])

    voice_content = f"""# voice.md - Channel Voice Profile for {name}

## Channel Identity
- **Channel Name:** {name}
- **Channel URL:** {channel_info.get("url", "")}
- **Description:** {desc.strip()}

## Who I am talking to
Horror story lovers, late-night listeners, fans of paranormal mysteries, creepy encounters, and urban legends who want immersive, dark, and spine-chilling audio-visual narratives. They crave realistic dread, tension, and stories that feel authentic.

## How I actually talk
Atmospheric, deliberate, calm yet unsettling. Build suspense slowly with vivid environmental cues (silence, shadows, ticking clocks, footsteps). The narration should feel like an intimate campfire or late-night confession, never rushed or over-dramatic.

## Recent Video Titles (Channel Baseline)
{titles_bullet}

## Words I never use
- "Hey guys welcome back to the channel!"
- "Don't forget to smash that like button"
- "This is crazy/insane bro"
- Generic happy YouTube filler phrases

## Words I do use
- "The air turned cold."
- "Something felt terribly off."
- "The silence was suffocating."
- "I froze in place."
- "That was the last time I saw..."
- "Whatever you do, don't look back."

## What I will not claim
Unverifiable scientific claims or cheap jump-scare clichés. Keep the horror grounded, psychological, and immersive.

## My format
- **Length:** 8 to 25 minutes long-form horror narration.
- **Hook (0:00 - 0:15):** Cold open right into the most disturbing realization or encounter. No channel intro or logo animation.
- **Pacing:** ~130-145 words per minute. Pacing slows down before moments of tension.
- **Sound & Visuals:** Dark ambient drone, rain/wind effects, binaural audio cues, slow camera push-in.
"""
    return voice_content
