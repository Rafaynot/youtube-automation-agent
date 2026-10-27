#!/usr/bin/env python3
"""web/server.py - Zero-dependency Web Server for the YouTube Agent UI.
Runs on Python standard library (http.server).
Serves the responsive dashboard and provides REST API endpoints.
"""
import os
import sys
import json
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import engine
from core import llm
from core import channel_fetcher
from core import studio_oauth
from config import resolver

STATIC_DIR = Path(__file__).resolve().parent / "static"

class YouTubeAgentHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def end_headers(self):
        # Enable CORS for local development
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            self.send_json({
                "status": "online",
                "has_gemini": bool(os.environ.get("GEMINI_API_KEY")),
                "has_openai": bool(os.environ.get("OPENAI_API_KEY")),
                "has_groq": bool(os.environ.get("GROQ_API_KEY")),
                "provider": llm.detect_provider()[0] or "prompt_export_mode"
            })
            return

        elif path == "/api/channel":
            ch_file = ROOT / "config" / "channel.json"
            if ch_file.exists():
                try:
                    data = json.loads(ch_file.read_text(encoding="utf-8"))
                    self.send_json(data)
                    return
                except Exception as e:
                    self.send_json({"error": str(e)}, status=500)
                    return
            self.send_json({"error": "No channel linked yet"}, status=404)
            return

        elif path == "/api/voice":
            content = resolver.load_voice_content()
            self.send_json({"content": content, "path": str(resolver.find_voice_file() or "")})
            return

        elif path == "/api/studio/status":
            token = studio_oauth.get_valid_access_token()
            has_creds = bool(studio_oauth.load_client_credentials()[0])
            self.send_json({
                "authenticated": bool(token),
                "has_credentials": has_creds
            })
            return

        elif path == "/api/studio/overview":
            overview = studio_oauth.fetch_channel_overview()
            self.send_json(overview)
            return

        elif path == "/api/studio/report":
            query = urllib.parse.parse_qs(parsed.query)
            days = query.get("days", ["28"])[0]
            report = studio_oauth.fetch_studio_report(days)
            self.send_json(report)
            return

        elif path == "/api/studio/trend":
            query = urllib.parse.parse_qs(parsed.query)
            days = query.get("days", ["28"])[0]
            trend = studio_oauth.fetch_studio_daily_trend(days)
            self.send_json({"days": days, "trend": trend})
            return

        elif path == "/api/studio/top-videos":
            query = urllib.parse.parse_qs(parsed.query)
            days = query.get("days", ["28"])[0]
            limit = int(query.get("limit", ["10"])[0])
            videos = studio_oauth.fetch_top_videos_studio(days=days, max_results=limit)
            self.send_json({"days": days, "videos": videos})
            return

        elif path == "/api/audit":
            res = engine.audit_channel()
            self.send_json(res)
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)
        
        try:
            body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            body = {}

        if path == "/api/hookscore":
            hook = body.get("hook", "").strip()
            if not hook:
                self.send_json({"error": "Hook text is required"}, status=400)
                return
            import importlib.util
            spec = importlib.util.spec_from_file_location("hookscore", ROOT / "skills" / "yt-script" / "hookscore.py")
            hookscore = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(hookscore)
            parts, verdict, name, hits = hookscore.score(hook)
            weakest = min(parts, key=parts.get)
            fix = hookscore.FIX.get(weakest, "")
            self.send_json({
                "hook": hook,
                "parts": parts,
                "verdict": verdict,
                "band": hookscore.band(verdict),
                "formula": name,
                "hits": hits,
                "weakest": weakest,
                "fix": fix,
                "raw_report": engine.score_hook(hook)
            })
            return

        elif path == "/api/title":
            title = body.get("title", "").strip()
            thumb = body.get("thumb", "").strip() or None
            import importlib.util
            spec = importlib.util.spec_from_file_location("title", ROOT / "skills" / "yt-package" / "title.py")
            title_tool = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(title_tool)
            res = title_tool.check(title, thumb=thumb)
            self.send_json(res)
            return

        elif path == "/api/link":
            url = body.get("url", "").strip()
            if not url:
                self.send_json({"error": "Channel URL is required"}, status=400)
                return
            info = channel_fetcher.fetch_channel_data(url)
            if "error" in info:
                self.send_json({"error": info["error"]}, status=400)
                return
            channel_fetcher.save_channel_config(info)
            voice = channel_fetcher.generate_voice_profile(info)
            (ROOT / "config" / "voice.md").write_text(voice, encoding="utf-8")
            self.send_json(info)
            return

        elif path == "/api/voice/save":
            content = body.get("content", "")
            (ROOT / "config" / "voice.md").write_text(content, encoding="utf-8")
            self.send_json({"success": True})
            return

        elif path == "/api/generate":
            skill_name = body.get("skill", "yt-script").strip()
            user_input = body.get("input", "").strip()
            if not user_input:
                self.send_json({"error": "Input prompt is required"}, status=400)
                return

            skill_file = ROOT / "skills" / skill_name / "SKILL.md"
            if not skill_file.exists():
                self.send_json({"error": f"Skill {skill_name} not found"}, status=404)
                return

            skill_instructions = skill_file.read_text(encoding="utf-8")
            voice_content = resolver.load_voice_content()

            system_prompt = f"""You are an elite YouTube expert acting as the YouTube Agent.
Follow the skill instructions strictly.
Do not invent facts, numbers or results.
Always finish with the gate question: 'ship it, or change it?'.

=== SKILL INSTRUCTIONS ({skill_name}) ===
{skill_instructions}

=== CREATOR VOICE PROFILE ===
{voice_content}
"""
            provider, _ = llm.detect_provider()
            if provider:
                success, response = llm.generate_ai_response(system_prompt, user_input)
                self.send_json({
                    "mode": "ai",
                    "provider": provider,
                    "success": success,
                    "result": response
                })
            else:
                full_prompt = f"{system_prompt}\n\n=== USER REQUEST ===\n{user_input}\n"
                (ROOT / "output").mkdir(exist_ok=True)
                (ROOT / "output" / "latest_prompt.txt").write_text(full_prompt, encoding="utf-8")
                self.send_json({
                    "mode": "prompt_export",
                    "provider": None,
                    "prompt": full_prompt,
                    "message": "API key not configured. Full prompt generated and ready to copy to ChatGPT / Gemini / Claude!"
                })
            return

        elif path == "/api/chapters":
            transcript = body.get("transcript", "").strip()
            if not transcript:
                self.send_json({"error": "Transcript text or SRT is required"}, status=400)
                return
            # Save temporary file and run chapters tool
            temp_srt = ROOT / "output" / "temp.srt"
            temp_srt.parent.mkdir(exist_ok=True)
            temp_srt.write_text(transcript, encoding="utf-8")
            out = engine.run_chapters(str(temp_srt), target=int(body.get("target", 7)))
            self.send_json({"chapters": out})
            return

        elif path == "/api/studio/credentials":
            client_id = body.get("client_id", "").strip()
            client_secret = body.get("client_secret", "").strip()
            if not client_id or not client_secret:
                self.send_json({"error": "client_id and client_secret are required"}, status=400)
                return
            creds = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            }
            CONFIG_DIR.mkdir(exist_ok=True)
            (CONFIG_DIR / "client_secret.json").write_text(json.dumps(creds, indent=2), encoding="utf-8")
            self.send_json({"success": True})
            return

        elif path == "/api/studio/auth":
            import threading
            threading.Thread(target=studio_oauth.authenticate_interactive, daemon=True).start()
            self.send_json({"status": "Authorization window opening in browser..."})
            return

        elif path == "/api/audit":
            res = engine.audit_channel()
            self.send_json(res)
            return

        elif path == "/api/seo":
            topic = body.get("topic", "").strip() or body.get("title", "").strip()
            if not topic:
                self.send_json({"error": "Topic or title is required"}, status=400)
                return
            res = engine.generate_seo_package(topic)
            self.send_json(res)
            return

        elif path == "/api/comment":
            comments = body.get("comments", "").strip()
            if not comments:
                self.send_json({"error": "Comment text is required"}, status=400)
                return
            res = engine.triage_comments_text(comments)
            self.send_json(res)
            return

        elif path == "/api/plan":
            hours = int(body.get("hours", 8))
            theme = body.get("theme", "Horror Storytelling")
            res = engine.plan_content_calendar(hours, theme)
            self.send_json(res)
            return

        elif path == "/api/shorts":
            src = body.get("text", "").strip() or body.get("topic", "").strip()
            if not src:
                self.send_json({"error": "Script, transcript, or topic text is required"}, status=400)
                return
            res = engine.extract_shorts_concepts(src)
            self.send_json(res)
            return

        elif path == "/api/deadair":
            transcript = body.get("transcript", "").strip()
            if not transcript:
                self.send_json({"error": "Transcript or SRT text is required"}, status=400)
                return
            temp_file = ROOT / "output" / "temp_deadair.srt"
            temp_file.parent.mkdir(exist_ok=True)
            temp_file.write_text(transcript, encoding="utf-8")
            out = engine.run_deadair(str(temp_file), floor=float(body.get("floor", 0.45)))
            self.send_json({"deadair": out})
            return

        elif path == "/api/retention":
            csv_text = body.get("csv", "").strip()
            if not csv_text:
                self.send_json({"error": "Retention CSV text is required"}, status=400)
                return
            temp_csv = ROOT / "output" / "temp_retention.csv"
            temp_csv.parent.mkdir(exist_ok=True)
            temp_csv.write_text(csv_text, encoding="utf-8")
            out = engine.run_retention(str(temp_csv))
            self.send_json({"retention": out})
            return

        self.send_json({"error": "Endpoint not found"}, status=404)

    def send_json(self, data, status=200):
        res = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(res)))
        self.end_headers()
        self.wfile.write(res)

def start_server(port=5000):
    server = ThreadingHTTPServer(("127.0.0.1", port), YouTubeAgentHandler)
    print(f"\n=======================================================")
    print(f"  YOUTUBE AGENT WEB DASHBOARD STARTED")
    print(f"  URL: http://localhost:{port}")
    print(f"=======================================================\n")
    return server

if __name__ == "__main__":
    port = 5000
    server = start_server(port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()
