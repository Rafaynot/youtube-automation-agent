#!/usr/bin/env python3
"""core/researcher.py - Live Competitor Spy & Reddit Viral Radar.
Scrapes trending horror, mystery, and thriller stories from Reddit communities
and tracks competitor channel uploads to auto-synthesize viral video concepts.
"""
import re
import json
import urllib.request
from pathlib import Path
from core import channel_fetcher
from core import llm
from config import resolver

ROOT = Path(__file__).resolve().parent.parent

REDDIT_COMMUNITIES = {
    "nosleep": {"name": "r/NoSleep", "desc": "Top viral psychological horror & scary experiences", "color": "#ff4500"},
    "LetsNotMeet": {"name": "r/LetsNotMeet", "desc": "True terrifying stalker & late-night encounters", "color": "#0079d3"},
    "Glitch_in_the_Matrix": {"name": "r/Glitch_in_the_Matrix", "desc": "Real inexplicable events, time slips & unexplainable phenomena", "color": "#7193ff"},
    "shortscarystories": {"name": "r/ShortScaryStories", "desc": "Bite-sized punchy horror concepts with sudden twists", "color": "#ff585b"},
    "DarkTales": {"name": "r/DarkTales", "desc": "Atmospheric dark fiction & grim folklore", "color": "#9b51e0"}
}

COMPETITOR_PRESETS = [
    {"handle": "@MrNightmare", "name": "Mr. Nightmare", "niche": "True Late Night Scary Stories"},
    {"handle": "@BeBusta", "name": "Be. Busta", "niche": "Disturbing Real Life Encounters"},
    {"handle": "@CreepCast", "name": "CreepCast", "niche": "Viral Creepypasta & Deep Dives"},
    {"handle": "@Unit522", "name": "Unit 522", "niche": "Horror Story Narrations"},
    {"handle": "@LazyMasquerade", "name": "Lazy Masquerade", "niche": "True Crime & Creepy Mysteries"}
]

def fetch_reddit_posts(subreddit: str = "nosleep", timeframe: str = "week", limit: int = 12) -> list[dict]:
    """Fetch top trending stories from a subreddit using public JSON API."""
    sub = subreddit.replace("r/", "").strip()
    if not sub:
        sub = "nosleep"
    
    url = f"https://old.reddit.com/r/{sub}/top.json?t={timeframe}&limit={limit}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            children = data.get("data", {}).get("children", [])
            
            posts = []
            for c in children:
                d = c.get("data", {})
                if d.get("stickied"): # Skip mod/pinned rules
                    continue
                
                title = d.get("title", "").strip()
                selftext = d.get("selftext", "").strip()
                ups = d.get("ups", 0)
                num_comments = d.get("num_comments", 0)
                permalink = "https://reddit.com" + d.get("permalink", "")
                author = d.get("author", "unknown")
                created_utc = d.get("created_utc", 0)
                
                # Preview snippet (first 350 chars)
                preview = re.sub(r"\s+", " ", selftext[:350]).strip()
                if len(selftext) > 350:
                    preview += "..."

                posts.append({
                    "id": d.get("id"),
                    "title": title,
                    "subreddit": f"r/{sub}",
                    "ups": ups,
                    "comments": num_comments,
                    "author": author,
                    "preview": preview,
                    "full_text": selftext[:2000],
                    "url": permalink,
                    "score_badge": f"🔥 {ups:,} Upvotes" if ups >= 1000 else f"⭐ {ups:,} Upvotes"
                })
            return posts
    except Exception as e:
        # Fallback sample horror stories if network is offline
        return [
            {
                "id": "sample_1",
                "title": "I Work The Night Shift At A Solitary Highway Diner. A Man Ordered Food For 3 Invisible Guests.",
                "subreddit": f"r/{sub}",
                "ups": 3420,
                "comments": 412,
                "author": "midnight_wanderer",
                "preview": "The diner sits on Route 9, forty miles from the nearest town. At 2:40 AM, an old black sedan parked outside with headlights off. The driver sat in booth 4 and placed 4 identical coffee cups on the table...",
                "full_text": "The diner sits on Route 9, forty miles from the nearest town. At 2:40 AM, an old black sedan parked outside with headlights off. The driver sat in booth 4 and placed 4 identical coffee cups on the table...",
                "url": "https://reddit.com/r/nosleep",
                "score_badge": "🔥 3,420 Upvotes"
            },
            {
                "id": "sample_2",
                "title": "I Found A Secret Emergency Broadcast Station While Hiking In The Fog.",
                "subreddit": f"r/{sub}",
                "ups": 2890,
                "comments": 319,
                "author": "radio_static99",
                "preview": "My radio picked up a looped warning signal on 104.3 FM. The automated voice was repeating my own coordinates and describing what I was wearing right now.",
                "full_text": "My radio picked up a looped warning signal on 104.3 FM. The automated voice was repeating my own coordinates and describing what I was wearing right now.",
                "url": "https://reddit.com/r/nosleep",
                "score_badge": "🔥 2,890 Upvotes"
            },
            {
                "id": "sample_3",
                "title": "My Security Camera Keeps Recording Me Asleep In Bed. But I Live Alone And Was Out Of Town.",
                "subreddit": f"r/{sub}",
                "ups": 4620,
                "comments": 580,
                "author": "hollow_sleeper",
                "preview": "I checked my phone notification while waiting at the airport gate in Dallas. The motion alert showed a figure in my bedroom at 3:15 AM wearing my winter jacket...",
                "full_text": "I checked my phone notification while waiting at the airport gate in Dallas. The motion alert showed a figure in my bedroom at 3:15 AM wearing my winter jacket...",
                "url": "https://reddit.com/r/nosleep",
                "score_badge": "🔥 4,620 Upvotes"
            }
        ]

def fetch_competitor_videos(handle_or_url: str) -> dict:
    """Fetch competitor channel info and recent video outliers."""
    data = channel_fetcher.fetch_channel_data(handle_or_url)
    if "error" in data:
        return data
    
    # Enrich videos with engagement estimation
    videos = data.get("recent_videos", [])
    return {
        "channel_name": data.get("channel_name", "Competitor Channel"),
        "handle": data.get("vanity_url", handle_or_url),
        "avatar": data.get("avatar", ""),
        "subscribers": data.get("subscriber_count", "Public Creator"),
        "video_count": data.get("video_count_public", ""),
        "videos": videos[:10]
    }

def synthesize_viral_ideas(research_items: list[dict], custom_niche: str = "Late-Night Atmospheric Horror Narration") -> list[dict]:
    """Uses Gemini AI to analyze scraped Reddit and competitor trends,
    generating 5 original, clickable video packages tailored for Fear Studio.
    """
    voice = resolver.load_voice_content() or "Atmospheric, dark, grounded, high-tension horror storytelling."
    
    # Build context from research items
    context_lines = []
    for idx, item in enumerate(research_items[:8], 1):
        if "title" in item:
            src = item.get("subreddit") or item.get("source") or "Competitor"
            ups = item.get("ups", "")
            preview = item.get("preview", "") or item.get("label", "")
            context_lines.append(f"{idx}. [{src} | {ups}] {item['title']}\n   Snippet: {preview[:200]}")
    
    research_text = "\n".join(context_lines) if context_lines else "General viral horror tropes: abandoned facilities, unexplained radio signals, night shift dread, solitary encounters."

    system_prompt = f"""You are the Lead Creative Director & YouTube Algorithm Strategist for Fear Studio (@FearStudio96).
Your job is to study viral trending Reddit stories and competitor data, and synthesize 5 COMPLETELY ORIGINAL, HIGH-CTR video concepts.

CHANNEL VOICE & IDENTITY:
{voice}

NICHE: {custom_niche}

RULES FOR EACH CONCEPT:
1. Title MUST be under 50 characters (or have the punch in the first 45 chars) so mobile YouTube does not truncate it.
2. Hook must be a gripping 0:15 opening line that creates an immediate curiosity loop without cheap clickbait.
3. Thumb Text must be 2 to 4 bold words, complementing (NOT repeating) the title.
4. Core Twist must describe the narrative escalation in 2-3 sentences.
5. Provide a 'script_seed' that can be directly passed into the Script Studio to write the full video.

Return ONLY a valid JSON array containing exactly 5 concept objects with these exact keys:
[
  {{
    "title": "Title Here",
    "formula": "Hook Formula Name (e.g. Broken Rule / Silent Stalker / Midnight Radio)",
    "hook_0_15": "Opening spoken line for first 15 seconds...",
    "thumb_text": "BOLD TEXT",
    "thumb_visual": "Visual description of thumbnail composition",
    "core_twist": "The narrative spine and psychological twist...",
    "source_inspo": "Inspired by Reddit r/nosleep trend / Competitor outlier",
    "script_seed": "A complete 1-paragraph story prompt ready for Script Studio..."
  }}
]
"""

    user_prompt = f"Trending Inspiration Data:\n{research_text}\n\nGenerate 5 original viral horror video concepts formatted as pure JSON array."

    provider, _ = llm.detect_provider()
    if provider:
        success, res = llm.generate_ai_response(system_prompt, user_prompt)
        if success and res:
            # Parse JSON safely
            clean_res = res.strip()
            if "```json" in clean_res:
                clean_res = clean_res.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_res:
                clean_res = clean_res.split("```")[1].split("```")[0].strip()
            
            try:
                ideas = json.loads(clean_res)
                if isinstance(ideas, list) and ideas:
                    return ideas
            except Exception:
                pass

    # High quality fallback ideas if AI offline
    return [
        {
            "title": "The Emergency Room That Never Closed",
            "formula": "Forbidden Location / Lingering Presence",
            "hook_0_15": "Hospital records say Wing C was sealed in 1989. So why was my patient assigned to Bed 14?",
            "thumb_text": "NEVER OPEN WING C",
            "thumb_visual": "Dark hospital corridor with emergency red lighting, door slightly ajar with shadow inside",
            "core_twist": "The protagonist discovers the patients admitted to Wing C aren't sick people; they are nurses and doctors who vanished during the 1989 blizzard.",
            "source_inspo": "Reddit r/nosleep hospital trend",
            "script_seed": "Write a 10-minute horror story for Fear Studio about an abandoned hospital wing where patient monitor alarms still trigger at 3:15 AM every night."
        },
        {
            "title": "I Listened to the Midnight Radio",
            "formula": "Unexplained Signal / Broadcast Dread",
            "hook_0_15": "Every radio station goes to static at 3:00 AM on this highway, except 94.7 FM.",
            "thumb_text": "DON'T TUNE IN",
            "thumb_visual": "Old car dashboard in pitch black night, radio dial glowing faint orange on 94.7 FM",
            "core_twist": "The radio host is taking live call-ins from drivers who disappeared on that same highway over the last 30 years.",
            "source_inspo": "Competitor outlier: CreepCast & Mr. Nightmare",
            "script_seed": "Write an atmospheric horror story for Fear Studio about a solo night truck driver who tunes into a phantom frequency describing accidents before they happen."
        },
        {
            "title": "Don't Look Through the Peep Hole",
            "formula": "Intrusion / Home Terror",
            "hook_0_15": "When someone knocks at 3:40 AM, never look through the peep hole. Look at the doorknob first.",
            "thumb_text": "IT'S NOT HUMAN",
            "thumb_visual": "Distorted fish-eye lens view of a darkened apartment hallway with an unnerving silhouette standing too close",
            "core_twist": "The knock isn't coming from outside the apartment door. The knocker is standing on the inside of the door, facing the hallway.",
            "source_inspo": "Reddit r/LetsNotMeet viral stalker concept",
            "script_seed": "Write a suspenseful 8-minute horror encounter for Fear Studio about an apartment resident who hears rhythmic knocks on their door late at night."
        },
        {
            "title": "I Guard the Appalachian Fire Tower",
            "formula": "Solitary Isolation / Woods Folklore",
            "hook_0_15": "Rule number one for Appalachian fire lookouts: if the trees start walking, turn off the lights.",
            "thumb_text": "RULES IN THE FOG",
            "thumb_visual": "Tower surrounded by dense misty mountain forest with a massive towering shape barely visible between the pines",
            "core_twist": "The fire lookout realizes the fires aren't caused by lightning, but by the creatures attempting to warm themselves when temperatures drop below zero.",
            "source_inspo": "Reddit r/nosleep wilderness horror trend",
            "script_seed": "Write an atmospheric Appalachian wilderness horror story for Fear Studio following a seasonal fire lookout who finds an old rulebook left by the previous guard."
        },
        {
            "title": "The Mirror Doesn't Blink",
            "formula": "Subtle Uncanny / Psychological Shock",
            "hook_0_15": "I thought my vision was blurry until I blinked, and the reflection in the mirror kept staring.",
            "thumb_text": "LOOK AWAY NOW",
            "thumb_visual": "Bathroom sink mirror showing the protagonist's back, but the face in the reflection is turned directly toward the camera",
            "core_twist": "The reflection isn't a supernatural entity; it's the protagonist trapped on the other side trying to warn the physical body not to leave the bathroom.",
            "source_inspo": "Reddit r/shortscarystories top rated",
            "script_seed": "Write a gripping 6-minute psychological horror story for Fear Studio about an antique silver vanity mirror that delays movements by two seconds."
        }
    ]
