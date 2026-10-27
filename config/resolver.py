#!/usr/bin/env python3
"""resolver.py - Helper to resolve voice profile and project configuration.
Works across any environment without Claude dependency.
"""
import os
from pathlib import Path

def get_project_root() -> Path:
    """Return the absolute path to the project root directory."""
    return Path(__file__).resolve().parent.parent

def find_voice_file() -> Path | None:
    """Find voice.md across standard priority locations:
    1. Local project: ./config/voice.md
    2. Local project root: ./voice.md
    3. User home: ~/.youtube-agent/voice.md
    4. Fallback legacy: ~/.claude/youtube/voice.md
    """
    root = get_project_root()
    candidates = [
        root / "config" / "voice.md",
        root / "voice.md",
        Path.home() / ".youtube-agent" / "voice.md",
        Path.home() / ".claude" / "youtube" / "voice.md"
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None

def load_voice_content() -> str:
    """Load the voice profile content if available, else empty string."""
    voice_path = find_voice_file()
    if voice_path and voice_path.exists():
        try:
            return voice_path.read_text(encoding="utf-8")
        except Exception:
            return ""
    return ""

if __name__ == "__main__":
    found = find_voice_file()
    if found:
        print(f"Voice file found at: {found}")
    else:
        print("No voice profile found.")
