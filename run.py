#!/usr/bin/env python3
"""run.py - Universal YouTube Agent CLI Runner.
Runs without Claude. Supports all 6 deterministic Python tools and all 11 AI skills.

Usage:
  python run.py hook "One line hook"
  python run.py title "My Video Title" --thumb "3 WORDS MAX"
  python run.py deadair transcript.srt [--floor 0.35]
  python run.py chapters transcript.srt [--target 8]
  python run.py retention retention.csv [--duration 600] [--transcript transcript.srt]
  python run.py swipe collected.json [--min 2.0]
  python run.py skill yt-script "How I built an AI agent in 24 hours"
  python run.py voice
  python run.py list
"""
import os
import sys
import argparse
from pathlib import Path

# Ensure Windows PowerShell/cmd prints UTF-8 cleanly
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core import engine
from core import llm
from core import channel_fetcher
from config import resolver

ALL_SKILLS = [
    "yt-script", "yt-package", "yt-edit", "yt-comment", "yt-plan",
    "yt-viral", "yt-retention", "yt-shorts", "yt-seo", "yt-chapters", "yt-audit"
]

SKILL_DESCRIPTIONS = {
    "yt-script": "Script from raw idea: 5 hooks off 21 formulas, scored, then spoken script.",
    "yt-package": "Title + thumbnail pairing linter (truncation, duplication, vagueness).",
    "yt-edit": "Transcript into edit decision list: dead air, filler cues, retakes.",
    "yt-comment": "Comment triage into 4 piles, replies in your voice, pin suggestion.",
    "yt-plan": "Weekly/monthly upload schedule matched to creator's actual hours.",
    "yt-viral": "Find what's working in your niche ranked by channel median multiple.",
    "yt-retention": "Audience retention export analysis (hook leak, cliffs, slide).",
    "yt-shorts": "Find self-contained shorts inside long video transcripts.",
    "yt-seo": "Search-driven description, focused tags, and 3 query targets.",
    "yt-chapters": "YouTube-validated chapters starting at 00:00 with 10s min length.",
    "yt-audit": "Channel audit ending in ONE actionable fix instead of twenty."
}

def print_banner():
    print(r"""
============================================================
  THE YOUTUBE AGENT - UNIVERSAL RUNNER (Claude-Free)
  11 Skills | 6 Deterministic Tools | Zero Overhead
============================================================
""")

def cmd_list(args):
    print("\n--- DETERMINISTIC TOOLS (Offline / Zero-API) ---")
    print("  python run.py hook \"<hook text>\"             Score hook on 5 properties")
    print("  python run.py title \"<title>\" [--thumb \"..\"] Lint title & thumbnail pairing")
    print("  python run.py deadair <transcript.srt>       Edit decision list (cuts/filler)")
    print("  python run.py chapters <transcript.srt>      Validated YouTube chapters")
    print("  python run.py retention <retention.csv>      Find cliffs, hook leaks & drops")
    print("  python run.py swipe <collected.json>         Outlier viral videos by multiple")
    
    print("\n--- 11 AGENT SKILLS ---")
    for name in ALL_SKILLS:
        print(f"  {name:<15} {SKILL_DESCRIPTIONS.get(name, '')}")
    print("\nRun any skill: python run.py skill <skill-name> \"<your idea / input>\"\n")

def cmd_voice(args):
    voice_path = resolver.find_voice_file()
    print(f"\nActive Voice Profile: {voice_path or 'None found'}")
    if voice_path:
        print("\n--- Profile Content Preview ---\n")
        content = resolver.load_voice_content()
        lines = content.splitlines()[:20]
        print("\n".join(lines))
        if len(content.splitlines()) > 20:
            print("... (truncated)")
    else:
        print("Create your voice profile at: config/voice.md")

def cmd_link(args):
    url = args.url.strip()
    print(f"\n[*] Connecting to YouTube and fetching channel info for: {url} ...")
    info = channel_fetcher.fetch_channel_data(url)
    if "error" in info:
        print(f"[!] Error linking channel: {info['error']}")
        return
    
    ch_path = channel_fetcher.save_channel_config(info)
    voice_content = channel_fetcher.generate_voice_profile(info)
    voice_path = ROOT / "config" / "voice.md"
    voice_path.write_text(voice_content, encoding="utf-8")
    
    print("\n" + "=" * 60)
    print(f"  SUCCESSFULLY LINKED CHANNEL: {info['name']}")
    print("=" * 60)
    print(f"  URL:           {info.get('url')}")
    print(f"  Recent Videos: {info.get('total_recent_videos', 0)} loaded")
    print(f"  Channel Data:  Saved to {ch_path}")
    print(f"  Voice Profile: Updated at {voice_path} (niche-optimized)")
    print("\nRecent Videos Found:")
    for i, v in enumerate(info.get("recent_videos", [])[:5], 1):
        print(f"   {i}. {v['title']} (ID: {v['videoId']})")
    print("=" * 60 + "\n")

def cmd_channel(args):
    ch_path = ROOT / "config" / "channel.json"
    if not ch_path.exists():
        print("\nNo channel linked yet. Link one using:")
        print("  python run.py link \"https://www.youtube.com/@FearStudio96\"\n")
        return
    import json
    try:
        data = json.loads(ch_path.read_text(encoding="utf-8"))
        print("\n" + "=" * 60)
        print(f"  LINKED CHANNEL: {data.get('name')}")
        print("=" * 60)
        print(f"  Handle/URL: {data.get('url')}")
        print(f"  Description: {data.get('description', '')[:180]}...")
        print(f"\nRecent Videos ({len(data.get('recent_videos', []))} total):")
        for i, v in enumerate(data.get("recent_videos", []), 1):
            print(f"  {i:2d}. {v['title']}")
            print(f"      Watch: {v['url']}")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"Error reading channel data: {e}")

def cmd_hook(args):
    target = args.hook_or_file
    if os.path.exists(target):
        out = engine.score_hook_file(target, as_json=args.json)
    else:
        out = engine.score_hook(target, as_json=args.json)
    print(out)

def cmd_title(args):
    out = engine.lint_title(args.title, thumb=args.thumb, as_json=args.json)
    print(out)

def cmd_deadair(args):
    out = engine.run_deadair(args.file, floor=args.floor, as_json=args.json)
    print(out)

def cmd_chapters(args):
    out = engine.run_chapters(args.file, target=args.target, as_json=args.json)
    print(out)

def cmd_retention(args):
    out = engine.run_retention(args.csv, duration=args.duration, transcript=args.transcript, as_json=args.json)
    print(out)

def cmd_swipe(args):
    out = engine.run_swipe(args.json_file, min_multiple=args.min, as_json=args.json)
    print(out)

def cmd_skill(args):
    skill_name = args.name.lower().strip()
    if skill_name.startswith("/"):
        skill_name = skill_name[1:]
    
    if skill_name not in ALL_SKILLS:
        print(f"Error: Unknown skill '{skill_name}'.")
        print(f"Available skills: {', '.join(ALL_SKILLS)}")
        sys.exit(1)
        
    skill_file = ROOT / "skills" / skill_name / "SKILL.md"
    if not skill_file.exists():
        print(f"Error: Skill definition file not found at {skill_file}")
        sys.exit(1)
        
    skill_instructions = skill_file.read_text(encoding="utf-8")
    voice_content = resolver.load_voice_content()
    
    # Read extra data files if available
    extra_context = ""
    if skill_name == "yt-script":
        hooks_json = ROOT / "skills" / "yt-script" / "hooks.json"
        if hooks_json.exists():
            extra_context += f"\n\nHOOK FORMULAS REFERENCE:\n{hooks_json.read_text(encoding='utf-8')[:3000]}...\n"

    # Assemble system prompt
    system_prompt = f"""You are an elite YouTube expert acting as the YouTube Agent.
Follow the skill instructions strictly.
Do not invent facts, numbers or results.
Always finish with the gate question: 'ship it, or change it?'.

=== SKILL INSTRUCTIONS ({skill_name}) ===
{skill_instructions}

=== CREATOR VOICE PROFILE ===
{voice_content if voice_content else "No custom voice profile set. Use natural, conversational, punchy creator style."}
{extra_context}
"""

    user_input = args.input
    # Check if input is a file path
    if os.path.exists(user_input):
        try:
            content = Path(user_input).read_text(encoding="utf-8", errors="replace")
            user_input = f"File content from {user_input}:\n\n{content}"
        except Exception:
            pass

    provider, _ = llm.detect_provider()
    
    if provider:
        print(f"[*] Provider detected: {provider.upper()}. Generating response...\n")
        success, response = llm.generate_ai_response(system_prompt, user_input)
        if success:
            print(response)
            return
        else:
            print(f"[!] AI generation failed: {response}")
            print("[*] Falling back to prompt export mode...\n")
            
    # Prompt Export Mode (Offline or No API Key)
    output_dir = ROOT / "output"
    output_dir.mkdir(exist_ok=True)
    prompt_file = output_dir / "latest_prompt.txt"
    
    full_prompt = f"{system_prompt}\n\n=== USER REQUEST ===\n{user_input}\n"
    prompt_file.write_text(full_prompt, encoding="utf-8")
    
    print("=" * 65)
    print("  NO LLM API KEY CONFIGURED - PROMPT READY TO COPY")
    print("=" * 65)
    print(f"\n[+] Full prompt assembled and saved to: {prompt_file}")
    print("\nYou can paste this prompt directly into:")
    print("  - ChatGPT (https://chat.openai.com)")
    print("  - Google Gemini (https://gemini.google.com)")
    print("  - Claude Web (https://claude.ai)")
    print("\nOr configure an API key to run automatically from this CLI:")
    print("  PowerShell: $env:GEMINI_API_KEY='your_api_key'")
    print("  CMD:        set GEMINI_API_KEY=your_api_key")
    print("  (Also supports OPENAI_API_KEY, GROQ_API_KEY, or local Ollama)")
    print("=" * 65)

def interactive_mode():
    print_banner()
    print("Choose an action:")
    print("  1. Score a Hook (yt-script hookscore)")
    print("  2. Lint Title & Thumbnail (yt-package)")
    print("  3. Run Edit Decision List on .srt (yt-edit)")
    print("  4. Generate Chapters from .srt (yt-chapters)")
    print("  5. Run an AI Skill (e.g. yt-script, yt-plan, etc.)")
    print("  6. View / Check Voice Profile")
    print("  7. List All Available Skills & Tools")
    print("  8. Link YouTube Channel (URL or @handle)")
    print("  9. View Linked Channel Details")
    print("  0. Exit")
    
    choice = input("\nEnter choice [0-9]: ").strip()
    if choice == "1":
        hook = input("Enter hook line to score: ").strip()
        if hook:
            print(engine.score_hook(hook))
    elif choice == "2":
        t = input("Enter title: ").strip()
        th = input("Enter thumbnail text (optional, press Enter to skip): ").strip()
        print(engine.lint_title(t, thumb=th if th else None))
    elif choice == "3":
        path = input("Enter path to .srt or transcript file: ").strip().strip('"')
        if os.path.exists(path):
            print(engine.run_deadair(path))
        else:
            print(f"File not found: {path}")
    elif choice == "4":
        path = input("Enter path to .srt or transcript file: ").strip().strip('"')
        if os.path.exists(path):
            print(engine.run_chapters(path))
        else:
            print(f"File not found: {path}")
    elif choice == "5":
        print(f"\nAvailable: {', '.join(ALL_SKILLS)}")
        sk = input("Enter skill name (e.g. yt-script): ").strip()
        inp = input("Enter your idea or prompt: ").strip()
        class DummyArgs:
            pass
        d = DummyArgs()
        d.name = sk
        d.input = inp
        cmd_skill(d)
    elif choice == "6":
        cmd_voice(None)
    elif choice == "7":
        cmd_list(None)
    elif choice == "8":
        url = input("Enter channel URL or handle (e.g. https://www.youtube.com/@FearStudio96): ").strip()
        if url:
            class DummyArgs: pass
            d = DummyArgs()
            d.url = url
            cmd_link(d)
    elif choice == "9":
        cmd_channel(None)
    else:
        print("Exiting.")

def main():
    parser = argparse.ArgumentParser(
        description="Universal YouTube Agent CLI Runner (Runs without Claude)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Command to run")
    
    # hook
    p_hook = subparsers.add_parser("hook", help="Score a hook or text file of hooks")
    p_hook.add_argument("hook_or_file", help="Hook string or path to hooks.txt")
    p_hook.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    p_hook.set_defaults(func=cmd_hook)
    
    # title
    p_title = subparsers.add_parser("title", help="Lint title and thumbnail pairing")
    p_title.add_argument("title", help="YouTube video title")
    p_title.add_argument("--thumb", default=None, help="Thumbnail text")
    p_title.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    p_title.set_defaults(func=cmd_title)
    
    # deadair
    p_deadair = subparsers.add_parser("deadair", help="Generate edit decision list from subtitle")
    p_deadair.add_argument("file", help="Path to .srt / .vtt / whisper .json")
    p_deadair.add_argument("--floor", type=float, default=0.45, help="Minimum silence pause floor in seconds")
    p_deadair.add_argument("--json", action="store_true", help="Output JSON cuts")
    p_deadair.set_defaults(func=cmd_deadair)
    
    # chapters
    p_chapters = subparsers.add_parser("chapters", help="Generate YouTube chapters from transcript")
    p_chapters.add_argument("file", help="Path to .srt transcript")
    p_chapters.add_argument("--target", type=int, default=7, help="Target number of chapters")
    p_chapters.add_argument("--json", action="store_true", help="Output JSON")
    p_chapters.set_defaults(func=cmd_chapters)
    
    # retention
    p_retention = subparsers.add_parser("retention", help="Analyze audience retention export")
    p_retention.add_argument("csv", help="Path to retention.csv")
    p_retention.add_argument("--duration", type=int, default=None, help="Video duration in seconds")
    p_retention.add_argument("--transcript", default=None, help="Path to transcript .srt")
    p_retention.add_argument("--json", action="store_true", help="Output JSON")
    p_retention.set_defaults(func=cmd_retention)
    
    # swipe
    p_swipe = subparsers.add_parser("swipe", help="Rank viral outliers from JSON")
    p_swipe.add_argument("json_file", help="Path to collected videos JSON")
    p_swipe.add_argument("--min", type=float, default=2.0, help="Minimum multiple over median")
    p_swipe.add_argument("--json", action="store_true", help="Output JSON")
    p_swipe.set_defaults(func=cmd_swipe)
    
    # skill
    p_skill = subparsers.add_parser("skill", help="Run any of the 11 AI skills")
    p_skill.add_argument("name", help="Skill name (e.g. yt-script, yt-package, yt-plan)")
    p_skill.add_argument("input", help="Topic, idea, prompt or file path")
    p_skill.set_defaults(func=cmd_skill)
    
    # voice
    p_voice = subparsers.add_parser("voice", help="Display active voice profile")
    p_voice.set_defaults(func=cmd_voice)
    
    # list
    p_list = subparsers.add_parser("list", help="List all skills and tools")
    p_list.set_defaults(func=cmd_list)
    
    # link
    p_link = subparsers.add_parser("link", help="Automatically link a YouTube channel by URL or @handle")
    p_link.add_argument("url", help="YouTube Channel URL or @handle (e.g. https://www.youtube.com/@FearStudio96)")
    p_link.set_defaults(func=cmd_link)

    # channel
    p_channel = subparsers.add_parser("channel", help="Show linked YouTube channel information and recent videos")
    p_channel.set_defaults(func=cmd_channel)
    
    # web
    def cmd_web(args):
        import app
        app.main()
    p_web = subparsers.add_parser("web", help="Start the beautiful Web UI Dashboard and open browser")
    p_web.set_defaults(func=cmd_web)

    # studio-auth
    def cmd_studio_auth(args):
        from core import studio_oauth
        studio_oauth.authenticate_interactive()
    p_sauth = subparsers.add_parser("studio-auth", help="Connect YouTube Studio via Google OAuth 2.0")
    p_sauth.set_defaults(func=cmd_studio_auth)

    # studio-report
    def cmd_studio_report(args):
        from core import studio_oauth
        import json
        rep = studio_oauth.fetch_studio_report(days=args.days)
        print("\n" + "=" * 60)
        print("  YOUTUBE STUDIO OFFICIAL ANALYTICS REPORT")
        print("=" * 60)
        print(json.dumps(rep, indent=2))
        print("=" * 60 + "\n")
    p_srep = subparsers.add_parser("studio-report", help="Fetch real-time Studio analytics report")
    p_srep.add_argument("--days", type=int, default=28, help="Number of past days (default: 28)")
    p_srep.set_defaults(func=cmd_studio_report)

    # audit (yt-audit)
    def cmd_audit(args):
        rep = engine.audit_channel()
        if "error" in rep:
            print(f"[!] Audit error: {rep['error']}")
            return
        print("\n" + "=" * 65)
        print(f"  END-TO-END CHANNEL AUDIT: {rep['channel_name']}")
        print("=" * 65)
        print(f"  Health Score:            {rep['health_score']}/100")
        print(f"  Videos Audited:          {rep['total_audited']}")
        print(f"  Mobile Cutoff Exposure:  {rep['mobile_cutoff_percentage']} of titles cut on phones")
        print("\n" + "-" * 65)
        print(f"  🔥 THE ONE BIGGEST FIX: {rep['primary_fix']['title']}")
        print("-" * 65)
        print(f"  Leak Identified: {rep['primary_fix']['leak']}")
        print(f"  What to do:      {rep['primary_fix']['action']}")
        print(f"  Expected Impact: {rep['primary_fix']['impact']}")
        print("\n  ✅ 3 Things Already Working Well:")
        for w in rep["working_well"]:
            print(f"     • {w}")
        print("\n  ⛔ What NOT to do yet:")
        print(f"     {rep['not_to_do_yet']}")
        print("\n  " + "=" * 65)
        print("  The Gate: ship it, or change it?")
        print("=" * 65 + "\n")
    p_audit = subparsers.add_parser("audit", help="Run end-to-end channel audit with the ONE biggest fix")
    p_audit.set_defaults(func=cmd_audit)

    # seo (yt-seo)
    def cmd_seo(args):
        res = engine.generate_seo_package(args.topic)
        print("\n" + "=" * 65)
        print(f"  SEO & SEARCH PACKAGING: {res['title']}")
        print("=" * 65)
        print("\n[Snippet Above The Fold - First 2 Lines]:")
        print(res["snippet_above_fold"])
        print("\n[3 Search Queries This Video Must Win]:")
        for q in res["target_queries"]:
            print(f"  • {q}")
        print(f"\n[Focused Disambiguation Tags ({res['tag_count']} total)]:")
        print(", ".join(res["tags"]))
        print("\n[Description Chapter Block]:")
        print(res["description_body"].strip())
        print("\n" + "=" * 65)
        print("The Gate: ship it, or change it?\n")
    p_seo = subparsers.add_parser("seo", help="Generate search-driven description, focused tags, and 3 query targets")
    p_seo.add_argument("topic", help="Video title or topic")
    p_seo.set_defaults(func=cmd_seo)

    # comment (yt-comment)
    def cmd_comment(args):
        text = args.text
        if os.path.exists(text):
            text = Path(text).read_text(encoding="utf-8", errors="replace")
        res = engine.triage_comments_text(text)
        print("\n" + "=" * 65)
        print("  COMMENT TRIAGE & VOICE REPLIES")
        print("=" * 65)
        for pile_name, items in res["piles"].items():
            if items:
                print(f"\n[{pile_name.upper().replace('_', ' ')} - {len(items)} comments]:")
                for it in items:
                    print(f"  • Comment: \"{it['comment']}\"")
                    if "reply" in it:
                        print(f"    Reply:   \"{it['reply']}\"")
                    print(f"    Action:  {it['action']}")
        print("\n" + "=" * 65 + "\n")
    p_com = subparsers.add_parser("comment", help="Triage comments into 4 piles and draft replies in voice")
    p_com.add_argument("text", help="Comment text or path to text file")
    p_com.set_defaults(func=cmd_comment)

    # plan (yt-plan)
    def cmd_plan(args):
        res = engine.plan_content_calendar(hours_per_week=args.hours, theme=args.theme)
        print("\n" + "=" * 65)
        print(f"  4-WEEK CONTENT CALENDAR ({res['creator_hours_per_week']} hrs/week)")
        print("=" * 65)
        print(f"Cadence: {res['cadence']} | Target: {res['monthly_target_uploads']} uploads\n")
        for w in res["weeks"]:
            print(f"Week {w['week']}: [{w['tier']}]")
            print(f"  Title:      {w['title_concept']}")
            print(f"  Format:     {w['format']} (~{w['production_time_hrs']} hrs)")
            print(f"  Schedule:   {w['upload_day']}")
            print(f"  Strategy:   {w['why']}\n")
        print("=" * 65 + "\n")
    p_plan = subparsers.add_parser("plan", help="Generate 4-week production calendar sized to your hours")
    p_plan.add_argument("--hours", type=int, default=8, help="Creator production hours per week (default: 8)")
    p_plan.add_argument("--theme", default="Horror & Suspense", help="Channel niche/theme")
    p_plan.set_defaults(func=cmd_plan)

    # shorts (yt-shorts)
    def cmd_shorts(args):
        src = args.input
        if os.path.exists(src):
            src = Path(src).read_text(encoding="utf-8", errors="replace")
        res = engine.extract_shorts_concepts(src)
        print("\n" + "=" * 65)
        print("  VIRAL SHORTS EXTRACTOR (3 CONCEPTS)")
        print("=" * 65)
        for s in res["shorts_extracted"]:
            print(f"\n[Short #{s['short_num']} - {s['duration']}]:")
            print(f"  0-3s Visual Hook: {s['hook_0_3s']}")
            print(f"  Spoken Script:   {s['spoken_script']}")
            print(f"  Loop Ending:     {s['loop_ending']}")
            print(f"  Format Notes:    {s['target_format']}")
        print("\n" + "=" * 65 + "\n")
    p_shorts = subparsers.add_parser("shorts", help="Extract 3 self-contained viral Shorts from long video or idea")
    p_shorts.add_argument("input", help="Topic, premise, or transcript file path")
    p_shorts.set_defaults(func=cmd_shorts)

    
    args = parser.parse_args()
    if not args.subcommand:
        interactive_mode()
    else:
        args.func(args)

if __name__ == "__main__":
    main()
