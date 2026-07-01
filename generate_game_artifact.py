#!/usr/bin/env python3
"""Generate raw model game artifacts from fixed comparison prompts."""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import requests


FROGGER_PROMPT = """Create a complete, self-contained single HTML file that is a playable version of the classic arcade game Frogger.

Requirements:
- Use HTML5 Canvas for the game
- Retro pixel art style with vibrant colors and clean sprites
- The frog can move up, down, left, and right
- Include moving cars on multiple lanes (different speeds and directions)
- Include a river section with floating logs and turtles that the frog can ride
- Add basic collision detection (frog dies when hit by a car or falls in water)
- Winning condition: frog reaches the top safe zone
- Score counter and lives system
- Simple sound effects using Web Audio API (optional but nice)
- Game should be fully playable

Controls:
- Keyboard: Arrow keys (or WASD)
- On-screen controller: Small, clean touch-friendly directional pad (D-pad) or four buttons at the bottom of the screen that works well on both mobile and desktop
- The controller should be clearly visible, responsive, and not overlap the game area

Additional polish:
- Responsive design that works on both desktop and mobile
- Restart button
- Simple instructions or title at the top
- Clean, modern retro aesthetic
- Make the code well-organized and commented where helpful

Output only the complete HTML code in one file. The game should run immediately when opened in any browser."""

SPACE_INVADERS_PROMPT = "Create a fully playable Space Invaders game in a single HTML file."


def extract_html(text: str) -> str:
    match = re.search(r"```(?:html)?\s*(.*?)```", text, flags=re.I | re.S)
    if match:
        return match.group(1).strip()
    lower = text.lower()
    for marker in ("<!doctype html", "<html"):
        idx = lower.find(marker)
        if idx >= 0:
            return text[idx:].strip()
    return text.strip()


def generate(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    prompt = FROGGER_PROMPT if args.game == "FROGGER" else SPACE_INVADERS_PROMPT
    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "chat_template_kwargs": {"thinking_mode": "disabled", "enable_thinking": False},
    }

    start = time.time()
    response = requests.post(
        args.endpoint.rstrip("/") + "/chat/completions",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=args.timeout,
    )
    elapsed = time.time() - start
    response.raise_for_status()
    data = response.json()
    choice = data["choices"][0]
    content = choice["message"].get("content") or ""
    html = extract_html(content)

    prefix = args.game
    (out_dir / f"{prefix}-response.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    (out_dir / f"{prefix}-raw-response.txt").write_text(content, encoding="utf-8")
    (out_dir / f"{prefix}.html").write_text(html, encoding="utf-8")

    usage = data.get("usage", {})
    meta = {
        "game": args.game,
        "endpoint": args.endpoint,
        "model": args.model,
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
        "finish_reason": choice.get("finish_reason"),
        "elapsed_seconds": round(elapsed, 3),
        "content_chars": len(content),
        "html_chars": len(html),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }
    (out_dir / f"{prefix}-meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(
        f"{args.game}: finish={meta['finish_reason']} "
        f"elapsed={elapsed:.1f}s completion_tokens={meta['completion_tokens']} "
        f"html_chars={meta['html_chars']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--game", choices=["FROGGER", "SPACE-INVADERS"], required=True)
    parser.add_argument("--max-tokens", type=int, required=True)
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--timeout", type=int, default=900)
    generate(parser.parse_args())


if __name__ == "__main__":
    main()
