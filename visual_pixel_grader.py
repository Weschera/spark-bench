#!/usr/bin/env python3
"""
visual_pixel_grader.py — Objective pixel-based visual artifact grader.

Renders HTML canvas/SVG animations in headless Chromium, captures screenshots
at multiple timestamps, and measures:

1. Render Score  — did anything appear on screen? (non-black pixel ratio)
2. Motion Score  — is it animating? (pixel delta between frames)
3. Color Score   — visual richness (unique non-black colors)
4. Coverage      — how much of the canvas is used

Final Visual Score = 0.35*Render + 0.35*Motion + 0.15*Color + 0.15*Coverage

A black screen scores ~0. A static image scores mid. A full animation scores high.

Usage:
    python3 visual_pixel_grader.py --artifacts-dir results/artifacts/
    python3 visual_pixel_grader.py --html-file path/to/VIS-01.html
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
from PIL import Image
import io

# ── Pixel analysis ────────────────────────────────────────────────────────── #

def analyze_screenshot(png_bytes, width, height):
    """Analyze PNG screenshot bytes. Returns dict of metrics."""
    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    pixels = list(img.getdata())
    total = width * height
    
    # Count non-black pixels (threshold: any channel > 15)
    non_black = 0
    color_set = set()
    
    for r, g, b, a in pixels:
        # Skip near-black (background)
        if r > 15 or g > 15 or b > 15:
            non_black += 1
            # Quantize colors to reduce noise (shift right by 4)
            color_set.add((r >> 4, g >> 4, b >> 4))
    
    render_ratio = non_black / total
    color_count = len(color_set)
    coverage = non_black / total  # same as render_ratio but separate concept
    
    return {
        "non_black_pixels": non_black,
        "total_pixels": total,
        "render_ratio": round(render_ratio, 4),
        "color_count": color_count,
        "coverage": round(coverage, 4),
        "pixel_data": pixels,  # Keep for motion computation
    }


def compute_motion(frame_a_pixels, frame_b_pixels):
    """Compute pixel-level delta between two frames. Returns motion ratio."""
    diffs = 0
    total = len(frame_a_pixels)
    
    for i in range(total):
        r1, g1, b1 = frame_a_pixels[i][0], frame_a_pixels[i][1], frame_a_pixels[i][2]
        r2, g2, b2 = frame_b_pixels[i][0], frame_b_pixels[i][1], frame_b_pixels[i][2]
        # Count as changed if any channel differs by > 20
        if abs(r1-r2) > 20 or abs(g1-g2) > 20 or abs(b1-b2) > 20:
            diffs += 1
    
    return round(diffs / total, 4) if total > 0 else 0.0


# ── Rendering ────────────────────────────────────────────────────────────── #

TIMESTAMPS = [0, 1, 2, 3]  # seconds to capture


def grade_html(html_path, width=1200, height=800):
    """Render HTML in headless Chromium, capture frames, compute visual score."""
    url = f"file://{os.path.abspath(html_path)}"
    frames = []
    
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path="/snap/bin/chromium",
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-software-rasterizer"]
        )
        page = browser.new_page(viewport={"width": width, "height": height})
        
        # Navigate and wait for load
        page.goto(url, wait_until="networkidle", timeout=10000)
        
        for t in TIMESTAMPS:
            if t > 0:
                page.wait_for_timeout(t * 1000)
            
            # Screenshot as PNG bytes
            png_bytes = page.screenshot(type="png")
            frames.append(png_bytes)
        
        browser.close()
    
    # Analyze each frame
    metrics = []
    for i, png_bytes in enumerate(frames):
        m = analyze_screenshot(png_bytes, width, height)
        m["timestamp"] = TIMESTAMPS[i]
        metrics.append(m)
    
    # Compute motion between consecutive frames
    motions = []
    for i in range(1, len(frames)):
        motion = compute_motion(metrics[i-1]["pixel_data"], metrics[i]["pixel_data"])
        motions.append(motion)
    
    # Remove pixel_data from metrics before output (too large for JSON)
    for m in metrics:
        del m["pixel_data"]
    
    # ── Compute final score ──────────────────────────────────────────────── #
    
    # 1. Render Score (0-100): did anything render?
    # Use the best frame (animations may start black then draw)
    best_render = max(m["render_ratio"] for m in metrics)
    # Normalize: 5% screen coverage = full render score (planets are small)
    render_score = min(100.0, (best_render / 0.05) * 100)
    
    # 2. Motion Score (0-100): is it animating?
    avg_motion = sum(motions) / len(motions) if motions else 0
    # Normalize: 1% pixel change between frames = full motion score
    motion_score = min(100.0, (avg_motion / 0.01) * 100)
    
    # 3. Color Score (0-100): visual richness
    best_colors = max(m["color_count"] for m in metrics)
    # Normalize: 50 unique color buckets = full color score
    color_score = min(100.0, (best_colors / 50) * 100)
    
    # 4. Coverage Score (0-100): how much of the screen is used
    best_coverage = max(m["coverage"] for m in metrics)
    # Normalize: 10% coverage = full score
    coverage_score = min(100.0, (best_coverage / 0.10) * 100)
    
    # Weighted final score
    final_score = (
        0.35 * render_score +
        0.35 * motion_score +
        0.15 * color_score +
        0.15 * coverage_score
    )
    
    return {
        "html_file": os.path.basename(html_path),
        "final_score": round(final_score, 1),
        "render_score": round(render_score, 1),
        "motion_score": round(motion_score, 1),
        "color_score": round(color_score, 1),
        "coverage_score": round(coverage_score, 1),
        "best_render_ratio": round(best_render, 4),
        "avg_motion": round(avg_motion, 4),
        "best_color_count": best_colors,
        "frames": metrics,
        "motions": motions,
    }


# ── Batch grading ────────────────────────────────────────────────────────── #

def find_gemma_artifacts(artifacts_dir):
    """Find all Gemma 4 visual artifacts."""
    artifacts_dir = Path(artifacts_dir)
    models = {}
    
    for run_dir in sorted(artifacts_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        name = run_dir.name
        if not name.startswith("Gemma-4-"):
            continue
        
        # Parse model name from directory
        # e.g. Gemma-4-12B-thinkOFF-57scen-20260625-210658
        parts = name.split("-")
        # Find the model size part (E2B, E4B, 12B, 26B-A4B, 31B)
        model_key = None
        for part in parts:
            if part in ("E2B", "E4B", "12B", "26B"):
                model_key = part
                break
            if part == "26B" and "A4B" in parts:
                model_key = "26B-A4B"
                break
        if not model_key:
            # Try to extract from full name
            if "E2B" in name:
                model_key = "E2B"
            elif "E4B" in name:
                model_key = "E4B"
            elif "12B" in name:
                model_key = "12B"
            elif "26B" in name:
                model_key = "26B-A4B"
            elif "31B" in name:
                model_key = "31B"
        
        if not model_key:
            continue
        
        # Find VIS HTML files
        vis_files = sorted(run_dir.glob("VIS-*.html"))
        if not vis_files:
            continue
        
        # Use the latest run for each model
        if model_key not in models or run_dir.name > models[model_key]["run_dir"]:
            models[model_key] = {
                "run_dir": run_dir.name,
                "path": str(run_dir),
                "vis_files": [(f.name, str(f)) for f in vis_files],
            }
    
    return models


def grade_all_gemma(artifacts_dir):
    """Grade all Gemma 4 visual artifacts and return results."""
    models = find_gemma_artifacts(artifacts_dir)
    
    if not models:
        print("No Gemma 4 artifacts found!")
        return
    
    # Order: E2B, E4B, 12B, 26B-A4B, 31B
    order = ["E2B", "E4B", "12B", "26B-A4B", "31B"]
    
    all_results = {}
    
    for model_key in order:
        if model_key not in models:
            continue
        
        info = models[model_key]
        print(f"\n{'='*60}")
        print(f"Grading Gemma 4 {model_key}")
        print(f"  Run: {info['run_dir']}")
        print(f"  Files: {[f[0] for f in info['vis_files']]}")
        print(f"{'='*60}")
        
        model_results = []
        for vis_name, vis_path in info["vis_files"]:
            print(f"\n  → {vis_name}...")
            try:
                result = grade_html(vis_path)
                result["model"] = model_key
                result["vis_id"] = vis_name.replace(".html", "")
                model_results.append(result)
                print(f"    Score: {result['final_score']}/100")
                print(f"    Render: {result['render_score']} | Motion: {result['motion_score']} | Color: {result['color_score']} | Coverage: {result['coverage_score']}")
            except Exception as e:
                print(f"    ERROR: {e}")
                model_results.append({
                    "model": model_key,
                    "vis_id": vis_name.replace(".html", ""),
                    "html_file": vis_name,
                    "final_score": 0.0,
                    "render_score": 0.0,
                    "motion_score": 0.0,
                    "color_score": 0.0,
                    "coverage_score": 0.0,
                    "error": str(e),
                })
        
        all_results[model_key] = model_results
    
    return all_results


def print_results_table(all_results):
    """Print a clean results table."""
    print(f"\n\n{'='*80}")
    print("VISUAL PIXEL GRADER — GEMMA 4 RESULTS")
    print(f"{'='*80}")
    
    # Per-model per-scenario
    print(f"\n{'Model':<10} {'VIS':<8} {'Score':>6} {'Render':>7} {'Motion':>7} {'Color':>6} {'Cover':>6}")
    print("-" * 60)
    
    model_scores = {}
    
    for model_key in ["E2B", "E4B", "12B", "26B-A4B", "31B"]:
        if model_key not in all_results:
            continue
        
        results = all_results[model_key]
        model_total = 0
        
        for r in results:
            print(f"{model_key:<10} {r['vis_id']:<8} {r['final_score']:>5.1f} {r['render_score']:>6.1f} "
                  f"{r['motion_score']:>6.1f} {r['color_score']:>5.1f} {r['coverage_score']:>5.1f}")
            model_total += r["final_score"]
        
        avg = model_total / len(results) if results else 0
        model_scores[model_key] = avg
        print(f"{'':>10} {'AVG':<8} {avg:>5.1f}")
        print()
    
    # Summary
    print(f"{'='*80}")
    print("SUMMARY — Average Visual Score by Model")
    print(f"{'='*80}")
    print(f"\n{'Model':<12} {'Visual Score':>12}")
    print("-" * 30)
    for model_key in ["E2B", "E4B", "12B", "26B-A4B", "31B"]:
        if model_key in model_scores:
            print(f"Gemma 4 {model_key:<6} {model_scores[model_key]:>10.1f}")
    
    return model_scores


# ── Main ──────────────────────────────────────────────────────────────────── #

def main():
    ap = argparse.ArgumentParser(description="Pixel-based visual artifact grader")
    ap.add_argument("--artifacts-dir", "-d", default="results/artifacts/",
                    help="Directory containing visual artifacts")
    ap.add_argument("--html-file", "-f", default=None,
                    help="Grade a single HTML file")
    ap.add_argument("--json-output", "-j", default=None,
                    help="Save results as JSON")
    args = ap.parse_args()
    
    if args.html_file:
        result = grade_html(args.html_file)
        print(json.dumps(result, indent=2))
        return
    
    all_results = grade_all_gemma(args.artifacts_dir)
    if all_results:
        model_scores = print_results_table(all_results)
        
        if args.json_output:
            output = {
                "models": {k: v for k, v in model_scores.items()},
                "details": all_results,
            }
            with open(args.json_output, "w") as f:
                json.dump(output, f, indent=2)
            print(f"\nResults saved to {args.json_output}")


if __name__ == "__main__":
    main()
