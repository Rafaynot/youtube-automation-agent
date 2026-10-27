#!/usr/bin/env python3
"""core/studio_oauth.py - YouTube Studio & Analytics API OAuth 2.0 Connector.
Zero external dependencies (uses standard library urllib & http.server).
Connects directly to:
- YouTube Analytics API (https://youtubeanalytics.googleapis.com/v2/reports)
- YouTube Data API v3 (https://www.googleapis.com/youtube/v3)
"""
import os
import sys
import json
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
TOKENS_FILE = CONFIG_DIR / "studio_tokens.json"
CLIENT_SECRET_FILE = CONFIG_DIR / "client_secret.json"

SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly"
]

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            OAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <html>
            <body style="font-family: sans-serif; background: #0a0c10; color: #fff; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0;">
                <div style="background: #12151c; border: 1px solid #ff2b55; padding: 40px; border-radius: 16px; text-align: center; max-width: 500px;">
                    <h1 style="color: #ff2b55; margin-bottom: 10px;">Authorization Successful!</h1>
                    <p style="color: #9aa5b8; font-size: 16px;">YouTube Studio is now connected to your YouTube Agent.</p>
                    <p style="color: #5e697d; font-size: 13px;">You can close this browser tab and return to the application.</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authorization failed or code missing.")

    def log_message(self, format, *args):
        # Suppress server terminal logs
        return

def load_client_credentials() -> tuple[str | None, str | None]:
    """Load client_id and client_secret from config/client_secret.json or env vars."""
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    if client_id and client_secret:
        return client_id, client_secret

    if CLIENT_SECRET_FILE.exists():
        try:
            data = json.loads(CLIENT_SECRET_FILE.read_text(encoding="utf-8"))
            # Standard Google client_secret format has 'installed' or 'web' root
            entry = data.get("installed") or data.get("web") or data
            return entry.get("client_id"), entry.get("client_secret")
        except Exception:
            pass

    return None, None

def authenticate_interactive(port=8088) -> bool:
    """Run interactive OAuth 2.0 flow using local web browser."""
    client_id, client_secret = load_client_credentials()
    if not client_id or not client_secret:
        print("\n[!] Error: Google OAuth credentials not found.")
        print(f"Please place your 'client_secret.json' inside: {CLIENT_SECRET_FILE}")
        print("Or set environment variables: YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET\n")
        return False

    redirect_uri = f"http://localhost:{port}"
    auth_params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent"
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(auth_params)}"

    print("\n" + "=" * 65)
    print("  CONNECTING YOUTUBE STUDIO VIA GOOGLE OAUTH 2.0")
    print("=" * 65)
    print(f"Opening browser for Google authorization...")
    print(f"If it doesn't open automatically, visit this URL:\n\n{auth_url}\n")
    print("=" * 65)

    server = HTTPServer(("127.0.0.1", port), OAuthCallbackHandler)
    server.timeout = 180  # 3 minutes timeout

    webbrowser.open(auth_url)

    # Wait for the single redirect request
    while OAuthCallbackHandler.auth_code is None:
        server.handle_request()

    code = OAuthCallbackHandler.auth_code
    if not code:
        print("[!] No authorization code received.")
        return False

    # Exchange code for tokens
    print("\n[*] Exchanging authorization code for API tokens...")
    token_url = "https://oauth2.googleapis.com/token"
    token_payload = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    data = urllib.parse.urlencode(token_payload).encode("utf-8")
    req = urllib.request.Request(token_url, data=data, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            tokens = json.loads(resp.read().decode("utf-8"))
            tokens["created_at"] = time.time()
            CONFIG_DIR.mkdir(exist_ok=True)
            TOKENS_FILE.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
            print(f"[+] Successfully connected! Tokens saved to: {TOKENS_FILE}\n")
            return True
    except Exception as e:
        print(f"[!] Error fetching tokens: {e}")
        return False

def get_valid_access_token() -> str | None:
    """Load access token and refresh it automatically if expired."""
    if not TOKENS_FILE.exists():
        return None

    try:
        tokens = json.loads(TOKENS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None

    created_at = tokens.get("created_at", 0)
    expires_in = tokens.get("expires_in", 3600)

    # If token is still valid (with 5 min safety buffer), return it
    if time.time() < (created_at + expires_in - 300):
        return tokens.get("access_token")

    # Otherwise refresh it
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        return None

    client_id, client_secret = load_client_credentials()
    if not client_id or not client_secret:
        return None

    token_url = "https://oauth2.googleapis.com/token"
    refresh_payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    data = urllib.parse.urlencode(refresh_payload).encode("utf-8")
    req = urllib.request.Request(token_url, data=data, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            new_tokens = json.loads(resp.read().decode("utf-8"))
            tokens["access_token"] = new_tokens["access_token"]
            tokens["expires_in"] = new_tokens.get("expires_in", 3600)
            tokens["created_at"] = time.time()
            TOKENS_FILE.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
            return tokens["access_token"]
    except Exception:
        return None

def parse_date_range(days):
    """Calculate start_date, end_date and label based on days parameter."""
    end_date = datetime.now().date()
    days_str = str(days).lower().strip()

    if days_str in ("lifetime", "all", "0"):
        start_date = datetime.strptime("2020-01-01", "%Y-%m-%d").date()
        period_label = "Lifetime"
    else:
        try:
            d_int = int(days)
        except ValueError:
            d_int = 28
        start_date = end_date - timedelta(days=d_int)
        period_label = f"Last {d_int} days"

    return start_date, end_date, period_label

def fetch_studio_report(days=28) -> dict:
    """Fetch official YouTube Studio Analytics report for the specified period (7, 28, 90, 365, or lifetime)."""
    token = get_valid_access_token()
    if not token:
        return {"error": "Not authenticated with YouTube Studio API. Run authorization first."}

    start_date, end_date, period_label = parse_date_range(days)

    metrics = [
        "views",
        "estimatedMinutesWatched",
        "averageViewDuration",
        "averageViewPercentage",
        "subscribersGained",
        "subscribersLost"
    ]

    params = {
        "ids": "channel==MINE",
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "metrics": ",".join(metrics)
    }

    url = f"https://youtubeanalytics.googleapis.com/v2/reports?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            headers = [h["name"] for h in res.get("columnHeaders", [])]
            rows = res.get("rows", [])
            
            if not rows:
                return {
                    "period": f"{start_date} to {end_date} ({period_label})",
                    "period_label": period_label,
                    "views": 0,
                    "watch_time_hours": 0,
                    "average_view_duration": "0m 0s",
                    "average_view_percentage": "0%",
                    "subscribers_net": 0,
                    "subscribers_gained": 0,
                    "subscribers_lost": 0,
                    "raw": {}
                }

            report = dict(zip(headers, rows[0]))
            
            views = report.get("views", 0)
            mins = report.get("estimatedMinutesWatched", 0)
            hours = round(mins / 60, 1)
            avg_dur = int(report.get("averageViewDuration", 0))
            avg_pct = round(report.get("averageViewPercentage", 0), 1)
            subs_gain = report.get("subscribersGained", 0)
            subs_lost = report.get("subscribersLost", 0)
            net_subs = subs_gain - subs_lost

            dur_str = f"{avg_dur // 60}m {avg_dur % 60}s"

            return {
                "period": f"{start_date} to {end_date} ({period_label})",
                "period_label": period_label,
                "days": str(days),
                "views": views,
                "watch_time_hours": hours,
                "average_view_duration": dur_str,
                "average_view_percentage": f"{avg_pct}%",
                "subscribers_net": net_subs,
                "subscribers_gained": subs_gain,
                "subscribers_lost": subs_lost,
                "raw": report
            }
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        return {"error": f"API Error {e.code}: {err}"}
    except Exception as e:
        return {"error": f"Failed to fetch report: {e}"}

def fetch_studio_daily_trend(days=28) -> list:
    """Fetch daily time-series data (views, watch time, subscribers) for charts."""
    token = get_valid_access_token()
    if not token:
        return []

    start_date, end_date, _ = parse_date_range(days)

    params = {
        "ids": "channel==MINE",
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "metrics": "views,estimatedMinutesWatched,subscribersGained",
        "dimensions": "day",
        "sort": "day"
    }

    url = f"https://youtubeanalytics.googleapis.com/v2/reports?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            rows = res.get("rows", [])
            trend = []
            for r in rows:
                day_str, v_count, mins, subs = r
                trend.append({
                    "date": day_str,
                    "views": v_count,
                    "watch_time_hours": round(mins / 60, 2),
                    "subscribers": subs
                })
            return trend
    except Exception:
        return []

def fetch_top_videos_studio(days=28, max_results=10) -> list:
    """Fetch top performing videos in the given period, enriched with titles & thumbnails."""
    token = get_valid_access_token()
    if not token:
        return []

    start_date, end_date, _ = parse_date_range(days)

    params = {
        "ids": "channel==MINE",
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "metrics": "views,estimatedMinutesWatched,averageViewDuration",
        "dimensions": "video",
        "sort": "-views",
        "maxResults": str(max_results)
    }

    url = f"https://youtubeanalytics.googleapis.com/v2/reports?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

    # Load local video catalog for title/thumb lookup
    catalog = {}
    ch_file = CONFIG_DIR / "channel.json"
    if ch_file.exists():
        try:
            ch_data = json.loads(ch_file.read_text(encoding="utf-8"))
            for v in ch_data.get("recent_videos", []):
                catalog[v.get("videoId")] = v
        except Exception:
            pass

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            rows = res.get("rows", [])
            results = []
            for r in rows:
                vid, v_count, mins, avg_dur = r
                cat_match = catalog.get(vid, {})
                title = cat_match.get("title") or f"Video {vid}"
                thumbnail = cat_match.get("thumbnail") or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
                v_url = cat_match.get("url") or f"https://www.youtube.com/watch?v={vid}"

                dur_m = int(avg_dur) // 60
                dur_s = int(avg_dur) % 60
                dur_str = f"{dur_m}m {dur_s}s"

                results.append({
                    "videoId": vid,
                    "title": title,
                    "thumbnail": thumbnail,
                    "url": v_url,
                    "views": v_count,
                    "watch_time_hours": round(mins / 60, 1),
                    "avg_duration": dur_str,
                    "avg_duration_sec": int(avg_dur)
                })
            return results
    except Exception:
        return []

def fetch_channel_overview() -> dict:
    """Fetch subscriber count, video count, avatar, and lifetime stats with fallback."""
    token = get_valid_access_token()
    
    # 1. Base from channel.json
    subscriber_count = "120 subscribers"
    video_count = "39 videos"
    channel_name = "Fear Studio"
    avatar = ""
    ch_file = CONFIG_DIR / "channel.json"
    if ch_file.exists():
        try:
            ch_data = json.loads(ch_file.read_text(encoding="utf-8"))
            subscriber_count = ch_data.get("subscriber_count") or subscriber_count
            video_count = ch_data.get("video_count_public") or video_count
            channel_name = ch_data.get("name") or channel_name
            avatar = ch_data.get("avatar") or avatar
        except Exception:
            pass

    # 2. Try official YouTube Data API v3 if enabled
    if token:
        try:
            req = urllib.request.Request(
                "https://www.googleapis.com/youtube/v3/channels?part=statistics&mine=true",
                headers={"Authorization": f"Bearer {token}"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("items", [])
                if items:
                    stats = items[0].get("statistics", {})
                    s_count = stats.get("subscriberCount")
                    v_count = stats.get("videoCount")
                    if s_count:
                        subscriber_count = f"{int(s_count):,} subscribers"
                    if v_count:
                        video_count = f"{int(v_count):,} videos"
        except Exception:
            # Silently use fallback when Data API v3 is disabled in project
            pass

    # 3. Lifetime Analytics report for total views and watch time
    lifetime_views = 67935
    lifetime_hours = 165.7
    lifetime_rep = fetch_studio_report("lifetime")
    if "views" in lifetime_rep:
        lifetime_views = lifetime_rep["views"]
        lifetime_hours = lifetime_rep["watch_time_hours"]

    return {
        "title": channel_name,
        "avatar": avatar,
        "subscriber_count": subscriber_count,
        "video_count": video_count,
        "lifetime_views": lifetime_views,
        "lifetime_hours": lifetime_hours,
        "authenticated": bool(token)
    }

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "auth":
        authenticate_interactive()
    else:
        rep = fetch_studio_report(28)
        print(json.dumps(rep, indent=2))
