#!/usr/bin/env python3
"""core/llm.py - Zero-dependency multi-provider LLM caller.
Uses standard library urllib.request to communicate with:
- Google Gemini (gemini-2.5-flash / gemini-1.5-flash)
- OpenAI (gpt-4o / gpt-4o-mini)
- Groq (llama-3.3-70b-versatile)
- Ollama (local open-source models)
- Anthropic Claude (claude-3-5-sonnet)
"""
import os
import json
import urllib.request
import urllib.error

def detect_provider() -> tuple[str | None, str | None]:
    """Detect available provider from environment variables."""
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini", os.environ["GEMINI_API_KEY"]
    if os.environ.get("OPENAI_API_KEY"):
        return "openai", os.environ["OPENAI_API_KEY"]
    if os.environ.get("GROQ_API_KEY"):
        return "groq", os.environ["GROQ_API_KEY"]
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic", os.environ["ANTHROPIC_API_KEY"]
    if os.environ.get("USE_OLLAMA") or os.environ.get("OLLAMA_HOST"):
        return "ollama", os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    return None, None

def call_gemini(api_key: str, system_prompt: str, user_prompt: str, model: str = "gemini-2.5-flash") -> str:
    """Call Google Gemini API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.7
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        return f"[Gemini API Error {e.code}]: {err}"
    except Exception as e:
        return f"[Gemini Request Failed]: {e}"

def call_openai_compatible(url: str, api_key: str, system_prompt: str, user_prompt: str, model: str) -> str:
    """Call OpenAI or compatible endpoints (e.g. Groq, Local)."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        return f"[API Error {e.code}]: {err}"
    except Exception as e:
        return f"[Request Failed]: {e}"

def call_ollama(host: str, system_prompt: str, user_prompt: str, model: str = "llama3") -> str:
    """Call local Ollama instance."""
    url = f"{host.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res["message"]["content"]
    except Exception as e:
        return f"[Ollama Error]: Could not reach Ollama at {url}. Is it running? Details: {e}"

def generate_ai_response(system_prompt: str, user_prompt: str) -> tuple[bool, str]:
    """Auto-detect provider and generate response."""
    provider, key_or_host = detect_provider()
    if not provider:
        return False, "NO_KEY"
    
    if provider == "gemini":
        return True, call_gemini(key_or_host, system_prompt, user_prompt)
    elif provider == "openai":
        return True, call_openai_compatible("https://api.openai.com/v1/chat/completions", key_or_host, system_prompt, user_prompt, "gpt-4o-mini")
    elif provider == "groq":
        return True, call_openai_compatible("https://api.groq.com/openai/v1/chat/completions", key_or_host, system_prompt, user_prompt, "llama-3.3-70b-versatile")
    elif provider == "ollama":
        return True, call_ollama(key_or_host, system_prompt, user_prompt)
    elif provider == "anthropic":
        url = "https://api.anthropic.com/v1/messages"
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "x-api-key": key_or_host,
            "anthropic-version": "2023-06-01"
        }
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return True, res["content"][0]["text"]
        except Exception as e:
            return False, f"[Anthropic API Error]: {e}"

    return False, "Unknown provider"
