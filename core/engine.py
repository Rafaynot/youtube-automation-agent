#!/usr/bin/env python3
"""core/engine.py - Wrapper for the 6 deterministic Python analysis tools.
Zero external dependencies. Invokes the tools cleanly and reliably.
"""
import os
import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import llm
from config import resolver

TOOLS = {
    "hook": ROOT / "skills" / "yt-script" / "hookscore.py",
    "title": ROOT / "skills" / "yt-package" / "title.py",
    "deadair": ROOT / "skills" / "yt-edit" / "deadair.py",
    "chapters": ROOT / "skills" / "yt-chapters" / "chapters.py",
    "retention": ROOT / "skills" / "yt-retention" / "retention.py",
    "swipe": ROOT / "skills" / "yt-viral" / "swipe.py",
}

def execute_tool(tool_name: str, args: list[str]) -> tuple[int, str]:
    """Execute one of the 6 tools via python subprocess."""
    if tool_name not in TOOLS:
        return 1, f"Unknown tool: {tool_name}. Available: {', '.join(TOOLS.keys())}"
    
    script_path = TOOLS[tool_name]
    if not script_path.exists():
        return 1, f"Script not found at: {script_path}"
    
    cmd = [sys.executable, str(script_path)] + args
    cwd = script_path.parent
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        output = proc.stdout if proc.stdout else proc.stderr
        return proc.returncode, output
    except Exception as e:
        return 1, f"Execution error: {e}"

def score_hook(hook: str, as_json: bool = False) -> str:
    """Score a hook using hookscore.py."""
    args = ["--hook", hook]
    if as_json:
        args.append("--json")
    code, out = execute_tool("hook", args)
    return out

def score_hook_file(file_path: str, as_json: bool = False) -> str:
    """Score hooks from a text file."""
    abs_path = str(Path(file_path).resolve())
    args = [abs_path]
    if as_json:
        args.append("--json")
    code, out = execute_tool("hook", args)
    return out

def lint_title(title: str, thumb: str | None = None, as_json: bool = False) -> str:
    """Lint a title and optional thumbnail pairing using title.py."""
    args = ["--title", title]
    if thumb:
        args.extend(["--thumb", thumb])
    if as_json:
        args.append("--json")
    code, out = execute_tool("title", args)
    return out

def run_deadair(file_path: str, floor: float = 0.45, as_json: bool = False) -> str:
    """Generate edit decision list from subtitle/transcript file."""
    abs_path = str(Path(file_path).resolve())
    args = [abs_path, "--floor", str(floor)]
    if as_json:
        args.append("--json")
    code, out = execute_tool("deadair", args)
    return out

def run_chapters(file_path: str, target: int = 7, as_json: bool = False) -> str:
    """Generate YouTube chapters from transcript."""
    abs_path = str(Path(file_path).resolve())
    args = [abs_path, "--target", str(target)]
    if as_json:
        args.append("--json")
    code, out = execute_tool("chapters", args)
    return out

def run_retention(csv_path: str, duration: int | None = None, transcript: str | None = None, as_json: bool = False) -> str:
    """Analyze YouTube audience retention CSV."""
    abs_csv = str(Path(csv_path).resolve())
    args = [abs_csv]
    if duration:
        args.extend(["--duration", str(duration)])
    if transcript:
        abs_ts = str(Path(transcript).resolve())
        args.extend(["--transcript", abs_ts])
    if as_json:
        args.append("--json")
    code, out = execute_tool("retention", args)
    return out

def run_swipe(json_path: str, min_multiple: float = 2.0, as_json: bool = False) -> str:
    """Calculate viral outliers from collected video data."""
    abs_path = str(Path(json_path).resolve())
    args = [abs_path, "--min", str(min_multiple)]
    if as_json:
        args.append("--json")
    code, out = execute_tool("swipe", args)
    return out

def audit_channel() -> dict:
    """End-to-end channel audit following skills/yt-audit/SKILL.md.
    Evaluates packaging, title structures, hook scores, and Studio performance.
    Ends in ONE decisive fix instead of twenty distractions.
    """
    import json
    import importlib.util

    ch_file = ROOT / "config" / "channel.json"
    if not ch_file.exists():
        return {"error": "No channel linked yet. Link a channel first via Channel Hub."}

    try:
        ch_data = json.loads(ch_file.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": f"Failed to read channel data: {e}"}

    videos = ch_data.get("recent_videos", [])
    if not videos:
        return {"error": "No videos found for this channel to audit."}

    # 1. Title diagnostics on recent titles
    spec_t = importlib.util.spec_from_file_location("title", ROOT / "skills" / "yt-package" / "title.py")
    title_mod = importlib.util.module_from_spec(spec_t)
    spec_t.loader.exec_module(title_mod)

    # 2. Hook score diagnostics on opening lines / titles
    spec_h = importlib.util.spec_from_file_location("hookscore", ROOT / "skills" / "yt-script" / "hookscore.py")
    hook_mod = importlib.util.module_from_spec(spec_h)
    spec_h.loader.exec_module(hook_mod)

    title_audits = []
    mobile_cutoff_count = 0
    desktop_cutoff_count = 0
    no_number_count = 0
    vague_count = 0
    total_score = 0

    for v in videos[:10]:
        t = v.get("title", "")
        res = title_mod.check(t)
        parts, verdict, formula, _ = hook_mod.score(t)
        res["hook_verdict"] = verdict
        res["hook_formula"] = formula
        res["thumbnail"] = v.get("thumbnail", "")
        title_audits.append(res)
        
        total_score += res.get("score", 70)
        chars = res.get("chars", 0)
        if chars > 40:
            mobile_cutoff_count += 1
        if chars > 60:
            desktop_cutoff_count += 1
        for issue_type, _ in res.get("issues", []):
            if issue_type == "no-number":
                no_number_count += 1
            elif issue_type == "vague":
                vague_count += 1

    sample_size = min(len(videos), 10)
    avg_score = round(total_score / sample_size) if sample_size else 70

    # 3. Pull studio performance if authenticated
    from core import studio_oauth
    studio_report = studio_oauth.fetch_studio_report(28)
    has_studio = "views" in studio_report

    # 4. Synthesize THE ONE BIGGEST FIX (as required by yt-audit philosophy)
    primary_fix = {}
    if mobile_cutoff_count >= (sample_size * 0.6):
        primary_fix = {
            "title": "Mobile Title Cutoff (Front-Load the Subject)",
            "leak": f"{mobile_cutoff_count} out of your last {sample_size} titles exceed 40 characters and get truncated on phones.",
            "action": "Keep the curiosity subject inside the first 38-40 characters. Put supporting details after the subject.",
            "impact": "Immediate increase in mobile feed CTR where >75% of YouTube viewing happens."
        }
    elif no_number_count >= (sample_size * 0.7):
        primary_fix = {
            "title": "Missing Concrete Anchors (Numbers & Names)",
            "leak": f"{no_number_count} out of {sample_size} titles lack concrete figures, numbers, or specific timeframes.",
            "action": "Anchor titles with a specific number or timeframe (e.g. '3 Creepy Stories', '16 Minutes Alone').",
            "impact": "Concrete figures trigger instant proof and curiosity over abstract titles."
        }
    elif has_studio and studio_report.get("average_view_percentage", "50%").replace("%", "").strip():
        pct = float(studio_report.get("raw", {}).get("averageViewPercentage", 35))
        if pct < 35:
            primary_fix = {
                "title": "Cold Open Hook Retention (0:00 - 0:15)",
                "leak": f"Audience retention averages {pct}%. Viewers are dropping before the story establishes stakes.",
                "action": "Eliminate channel introductions. The opening sentence must plunge the listener directly into the danger.",
                "impact": "Locks viewers past the 30-second cliff into high-retention territory."
            }
        else:
            primary_fix = {
                "title": "Thumbnail & Title Anti-Duplication",
                "leak": "Thumbnail texts must contrast the title rather than repeating it.",
                "action": "Limit thumbnail text to 3 punchy words that create a curiosity gap against the title.",
                "impact": "Doubles the click surface by delivering two distinct curiosity triggers."
            }
    else:
        primary_fix = {
            "title": "Cold Open Hook Retention (0:00 - 0:15)",
            "leak": "Viewer attention is fragile in the first 15 seconds.",
            "action": "Plunge directly into the chilling atmosphere. No logo animation or preamble.",
            "impact": "Maximizes average watch duration across the horror storytelling catalog."
        }

    # 3 Things Working Well
    working_well = [
        "Atmospheric Niche Focus: Strong alignment with late-night horror storytelling.",
        f"Catalog Depth: {len(videos)} videos providing immediate binge potential.",
        "Thumbnail Contrast: Dark cinematic visual tones with focal red accents."
    ]

    # What NOT to do yet
    not_to_do = "Do NOT pivot to unrelated trends or rush daily uploads. For horror storytelling, audio quality, tension pacing, and thumbnail readability at mobile size matter 10x more than upload frequency."

    return {
        "channel_name": ch_data.get("name", "Channel"),
        "channel_url": ch_data.get("url", ""),
        "total_audited": sample_size,
        "health_score": avg_score,
        "mobile_cutoff_percentage": f"{round((mobile_cutoff_count / sample_size) * 100)}%",
        "primary_fix": primary_fix,
        "working_well": working_well,
        "not_to_do_yet": not_to_do,
        "title_audits": title_audits,
        "gate_question": "ship it, or change it?"
    }

def generate_seo_package(topic_or_title: str) -> dict:
    """Generate search-driven description, focused tags, and 3 query targets (yt-seo)."""
    t = topic_or_title.strip()
    clean_words = [w.capitalize() for w in t.replace("—", " ").replace("-", " ").split() if len(w) > 3][:6]
    main_topic = " ".join(clean_words) or t

    # Fallback template
    snippet = f"A true horror encounter exploring {t.lower()}. What really happened when the silence was broken, and why you should never look back."
    queries = [
        f"{t.lower()}",
        f"{' '.join(clean_words[:3]).lower()} true horror stories",
        f"creepy scary stories to listen to alone"
    ]
    tags = [
        t.lower(), f"{t.lower()} story", "fear studio", "true horror stories",
        "creepy stories", "scary stories", "paranormal encounter", "horror narration",
        "stories to sleep to", "urban legend", "terrifying encounter", "dark stories", "nightmare fuel"
    ]
    desc_body = f"""{snippet}

🔔 Subscribe to Fear Studio for immersive horror storytelling:
https://www.youtube.com/@FearStudio96

TIMESTAMPS:
00:00 The Cold Open
01:15 The First Realization
04:30 What Was Left Behind
08:00 The Final Warning

⚠️ Viewer discretion is advised. Best experienced with headphones in the dark.

#HorrorStories #ScaryStories #FearStudio #CreepyTale
"""

    # AI Enhancement if Gemini or other provider available
    provider, _ = llm.detect_provider()
    if provider:
        voice = resolver.load_voice_content()
        seo_prompt = f"""You are an elite YouTube SEO strategist following skills/yt-seo/SKILL.md.
Video Topic / Title: {t}
Creator Voice Profile:
{voice if voice else "Dark, atmospheric storytelling"}

Generate a high-ranking YouTube SEO package strictly as a JSON object with:
- "snippet_above_fold": exactly 2 sentences confirming the click without giving away the ending.
- "target_queries": array of 3 specific search queries a real person types that this video should win.
- "tags": array of 12-15 focused tags.
- "description_body": formatted complete YouTube description including timestamps, call to action, and hashtags.

Output ONLY valid raw JSON with keys: snippet_above_fold, target_queries, tags, description_body. No code fences."""
        success, resp = llm.generate_ai_response("You are an expert YouTube SEO assistant. Output only JSON.", seo_prompt)
        if success:
            try:
                txt = resp.strip()
                if txt.startswith("```"):
                    txt = txt.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                parsed = json.loads(txt)
                if "tags" in parsed and "description_body" in parsed:
                    return {
                        "title": t,
                        "snippet_above_fold": parsed.get("snippet_above_fold", snippet),
                        "target_queries": parsed.get("target_queries", queries),
                        "tags": parsed.get("tags", tags),
                        "tag_count": len(parsed.get("tags", tags)),
                        "description_body": parsed.get("description_body", desc_body),
                        "gate_question": "ship it, or change it?"
                    }
            except Exception:
                pass

    return {
        "title": t,
        "snippet_above_fold": snippet,
        "target_queries": queries,
        "tags": tags,
        "tag_count": len(tags),
        "description_body": desc_body,
        "gate_question": "ship it, or change it?"
    }

def triage_comments_text(comments_text: str) -> dict:
    """Triage YouTube comments into 4 piles and draft replies in channel voice (yt-comment)."""
    lines = [l.strip() for l in comments_text.splitlines() if l.strip()]

    # AI Enhancement if Gemini available
    provider, _ = llm.detect_provider()
    if provider and lines:
        voice = resolver.load_voice_content()
        comment_prompt = f"""You are a YouTube comment strategist following skills/yt-comment/SKILL.md.
Creator Voice Profile:
{voice if voice else "Dark, atmospheric storytelling"}

Triage these viewer comments into 4 piles and draft in-character replies:
COMMENTS:
{comments_text}

Output ONLY valid raw JSON with this structure:
{{
  "piles": {{
    "worth_answering": [
      {{"comment": "...", "reply": "...", "action": "..."}}
    ],
    "pin_candidate": [
      {{"comment": "...", "reply": "...", "action": "..."}}
    ],
    "praise": [
      {{"comment": "...", "reply": "...", "action": "..."}}
    ],
    "trash": [
      {{"comment": "...", "action": "Ignore / Hide silently"}}
    ]
  }}
}}
No markdown fences."""
        success, resp = llm.generate_ai_response("You are an expert YouTube community manager. Output only JSON.", comment_prompt)
        if success:
            try:
                txt = resp.strip()
                if txt.startswith("```"):
                    txt = txt.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                parsed = json.loads(txt)
                if "piles" in parsed:
                    return {
                        "total_analyzed": len(lines),
                        "piles": parsed["piles"],
                        "gate_question": "ship it, or change it?"
                    }
            except Exception:
                pass
    
    # Fallback rule-based triage
    piles = {
        "worth_answering": [],
        "pin_candidate": [],
        "praise": [],
        "trash": []
    }

    troll_words = {"fake", "boring", "trash", "bad", "sub4sub", "check out my channel", "first"}
    question_words = {"?", "how", "what", "where", "why", "who", "when", "is this real"}
    insight_words = {"atmosphere", "audio", "narrat", "chills", "goosebumps", "reminds me of", "personal"}

    for line in lines:
        l_lower = line.lower()
        if any(w in l_lower for w in troll_words) and "?" not in line:
            piles["trash"].append({
                "comment": line,
                "action": "Ignore / Hide silently. Do not debate in public."
            })
        elif "?" in line or any(w in l_lower for w in question_words):
            piles["worth_answering"].append({
                "comment": line,
                "reply": f"The details are exactly as recorded. More will be unraveled in the next story.",
                "action": "Reply in calm, atmospheric channel voice."
            })
        elif any(w in l_lower for w in insight_words) or len(line) > 80:
            piles["pin_candidate"].append({
                "comment": line,
                "reply": "Thank you for listening in the dark. Pinning this for tonight's listeners.",
                "action": "Pin to top of comment section to set the tone."
            })
        else:
            piles["praise"].append({
                "comment": line,
                "reply": "Glad the tension landed. Keep the lights on tonight.",
                "action": "Heart & brief acknowledgment."
            })

    return {
        "total_analyzed": len(lines),
        "piles": piles,
        "gate_question": "ship it, or change it?"
    }

def plan_content_calendar(hours_per_week: int = 8, theme: str = "Horror & Suspense") -> dict:
    """Generate 4-week production plan sized to actual creator capacity (yt-plan)."""
    hours = max(4, hours_per_week)

    # AI Enhancement if Gemini available
    provider, _ = llm.detect_provider()
    if provider:
        voice = resolver.load_voice_content()
        plan_prompt = f"""You are an elite YouTube programming strategist following skills/yt-plan/SKILL.md.
Theme: {theme}
Creator Available Hours/Week: {hours}
Creator Voice / Channel context:
{voice if voice else "Dark atmospheric horror storytelling"}

Design a realistic 4-week upload calendar prioritized into 4 tiers:
Week 1: Search Anchor (Evergreen)
Week 2: Bread & Butter (Core Community)
Week 3: Trend / Folklore / Seasonal
Week 4: Experimental Swing (Outlier Potential)

Output ONLY valid JSON:
{{
  "cadence": "Weekly (Every Friday evening)",
  "weeks": [
    {{
      "week": 1,
      "tier": "Search Anchor (Evergreen)",
      "title_concept": "Specific compelling video title",
      "format": "e.g. Long-form 12-16 min narration",
      "production_time_hrs": {round(hours * 0.8, 1)},
      "upload_day": "Friday 7:00 PM",
      "why": "High search volume premise"
    }},
    {{
      "week": 2,
      "tier": "Bread & Butter (Core Community)",
      "title_concept": "Specific core video title",
      "format": "Psychological tension build (10-12 mins)",
      "production_time_hrs": {round(hours * 0.8, 1)},
      "upload_day": "Friday 7:00 PM",
      "why": "Feeds core subscriber retention"
    }},
    {{
      "week": 3,
      "tier": "Trend / Folklore / Seasonal",
      "title_concept": "Folklore or trend video title",
      "format": "Deep dive investigation (14 mins)",
      "production_time_hrs": {round(hours * 0.9, 1)},
      "upload_day": "Friday 7:00 PM",
      "why": "Viral folklore appeal"
    }},
    {{
      "week": 4,
      "tier": "Experimental Swing (Outlier Potential)",
      "title_concept": "High curiosity viral swing title",
      "format": "Fast-paced escalation (8 mins)",
      "production_time_hrs": {round(hours * 0.7, 1)},
      "upload_day": "Friday 7:00 PM",
      "why": "Recommendation algorithm breakout potential"
    }}
  ]
}}
No markdown fences."""
        success, resp = llm.generate_ai_response("You are an expert YouTube planner. Output only JSON.", plan_prompt)
        if success:
            try:
                txt = resp.strip()
                if txt.startswith("```"):
                    txt = txt.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                parsed = json.loads(txt)
                if "weeks" in parsed and len(parsed["weeks"]) == 4:
                    return {
                        "creator_hours_per_week": hours,
                        "monthly_target_uploads": 4,
                        "theme": theme,
                        "cadence": parsed.get("cadence", "Weekly (Every Friday evening)"),
                        "weeks": parsed["weeks"],
                        "gate_question": "ship it, or change it?"
                    }
            except Exception:
                pass
    
    # Fallback static calendar
    weeks = [
        {
            "week": 1,
            "tier": "Search Anchor (Evergreen)",
            "title_concept": "3 Creepy Encounters in the Woods You Shouldn't Hear Alone",
            "format": "Long-form 12-16 min narration",
            "production_time_hrs": round(hours * 0.8, 1),
            "upload_day": "Friday 7:00 PM",
            "why": "High search volume keyword for evergreen long-tail views."
        },
        {
            "week": 2,
            "tier": "Bread & Butter (Core Community)",
            "title_concept": "The Night Shift Was Empty... Until 3:00 AM",
            "format": "Psychological tension build (9-12 mins)",
            "production_time_hrs": round(hours * 0.8, 1),
            "upload_day": "Friday 7:00 PM",
            "why": "Reliable high-retention premise that feeds the core subscriber base."
        },
        {
            "week": 3,
            "tier": "Trend / Folklore / Seasonal",
            "title_concept": "The True Story Behind the Midnight Whistling Ritual",
            "format": "Deep-dive atmospheric story (14 mins)",
            "production_time_hrs": round(hours * 0.9, 1),
            "upload_day": "Friday 7:00 PM",
            "why": "Capitalizes on viral folklore curiosity."
        },
        {
            "week": 4,
            "tier": "Experimental Swing (Outlier Potential)",
            "title_concept": "I Found a Secret Door in My Basement [True Story]",
            "format": "First-person intense escalation (8 mins fast-paced)",
            "production_time_hrs": round(hours * 0.7, 1),
            "upload_day": "Friday 7:00 PM",
            "why": "High click-through swing aiming for feed algorithm recommendations."
        }
    ]

    return {
        "creator_hours_per_week": hours,
        "monthly_target_uploads": 4,
        "theme": theme,
        "cadence": "Weekly (Every Friday evening)",
        "weeks": weeks,
        "gate_question": "ship it, or change it?"
    }

def extract_shorts_concepts(text_or_idea: str) -> dict:
    """Extract 3 self-contained viral Shorts from long video transcript or premise (yt-shorts)."""
    src = text_or_idea.strip()

    # AI Enhancement if Gemini available
    provider, _ = llm.detect_provider()
    if provider:
        shorts_prompt = f"""You are a short-form YouTube video specialist following skills/yt-shorts/SKILL.md.
Extract 3 self-contained, punchy viral Shorts from this source text:
SOURCE:
{src}

Output ONLY valid JSON with this structure:
{{
  "shorts": [
    {{
      "short_num": 1,
      "hook_0_3s": "First 3 seconds visual/verbal hook",
      "duration": "45 seconds (~105 words)",
      "spoken_script": "The spoken words with tension",
      "loop_ending": "Ending line that loops into the hook",
      "target_format": "Vertical 9:16 framing notes"
    }},
    {{
      "short_num": 2,
      "hook_0_3s": "...",
      "duration": "50 seconds (~115 words)",
      "spoken_script": "...",
      "loop_ending": "...",
      "target_format": "..."
    }},
    {{
      "short_num": 3,
      "hook_0_3s": "...",
      "duration": "40 seconds (~95 words)",
      "spoken_script": "...",
      "loop_ending": "...",
      "target_format": "..."
    }}
  ]
}}
No markdown fences."""
        success, resp = llm.generate_ai_response("You are an expert Shorts writer. Output only JSON.", shorts_prompt)
        if success:
            try:
                txt = resp.strip()
                if txt.startswith("```"):
                    txt = txt.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                parsed = json.loads(txt)
                if "shorts" in parsed and len(parsed["shorts"]) > 0:
                    return {
                        "source_summary": src[:120] + "...",
                        "shorts_extracted": parsed["shorts"],
                        "gate_question": "ship it, or change it?"
                    }
            except Exception:
                pass
    
    # Fallback templates
    shorts = [
        {
            "short_num": 1,
            "hook_0_3s": "Look closely at the window behind him...",
            "duration": "45 seconds (~105 words)",
            "spoken_script": f"It was 2:40 in the morning when the floorboards began to groan. At first, it sounded like ordinary settling. But then came three deliberate knocks—not on the door, but from inside the closet. Whatever you do, don't look up.",
            "loop_ending": "...and that was when the knocking started again.",
            "target_format": "Vertical 9:16, dark ambient rain, slow zoom"
        },
        {
            "short_num": 2,
            "hook_0_3s": "The police report had one detail they never made public.",
            "duration": "50 seconds (~115 words)",
            "spoken_script": f"When investigators entered the abandoned cabin, the table was set for two. The food was still warm, but the dust on the floor had no footsteps leaving the room. The only footprint... was on the ceiling.",
            "loop_ending": "...leading straight into the dark attic above.",
            "target_format": "Vertical 9:16, eerie sound drone, pulsing text"
        },
        {
            "short_num": 3,
            "hook_0_3s": "If you hear your name called in the woods, never answer.",
            "duration": "40 seconds (~95 words)",
            "spoken_script": f"My grandfather gave me only one rule before entering the old timber line: if you hear someone calling your voice from behind you, never turn around. Because it's not trying to find you—it's trying to make you look.",
            "loop_ending": "...and whatever was calling was getting closer.",
            "target_format": "Vertical 9:16, binaural whisper audio, dark forest visuals"
        }
    ]

    return {
        "source_summary": src[:120] + "...",
        "shorts_extracted": shorts,
        "gate_question": "ship it, or change it?"
    }
