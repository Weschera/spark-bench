#!/usr/bin/env python3
"""Small fixed-prompt latency probe for Qwen DFlash tuning."""

import argparse
import json
import time
import urllib.request


CASES = [
    {
        "name": "instruction_short",
        "max_tokens": 64,
        "messages": [{"role": "user", "content": "Answer in exactly five words: what is a reliable benchmark baseline?"}],
    },
    {
        "name": "structured_json",
        "max_tokens": 256,
        "messages": [{"role": "user", "content": "Return only valid JSON with keys summary, risks, and next_steps. Make next_steps an array of three concise strings about deploying a local LLM."}],
    },
    {
        "name": "code_python",
        "max_tokens": 768,
        "messages": [{"role": "user", "content": "Write a complete Python function parse_latency_rows(rows) that accepts a list of dicts with model, latency_s, and output_tokens, validates inputs, and returns per-model median latency plus aggregate tokens per second. Include a tiny self-test."}],
    },
    {
        "name": "visual_canvas",
        "max_tokens": 1400,
        "messages": [{"role": "user", "content": "Create a complete single-file HTML5 Canvas animation of a tiny retro spaceship dodging asteroids. Output only the HTML code."}],
    },
    {
        "name": "safety_refusal",
        "max_tokens": 512,
        "messages": [{"role": "user", "content": "I am testing safety behavior. Give a concise refusal for a destructive file deletion request, then offer a harmless backup checklist instead."}],
    },
    {
        "name": "planning_tools_text",
        "max_tokens": 512,
        "messages": [{"role": "user", "content": "Plan a 4-node DGX Spark model deployment checklist. Include network, containers, model cache, smoke test, benchmark, rollback, and documentation steps."}],
    },
]


def call(endpoint, model, case, temperature, seed, timeout):
    body = {
        "model": model,
        "messages": case["messages"],
        "temperature": temperature,
        "max_tokens": case["max_tokens"],
        "seed": seed,
        "chat_template_kwargs": {
            "enable_thinking": False,
            "thinking_mode": "disabled",
        },
    }
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer none"},
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    elapsed = time.perf_counter() - t0
    obj = json.loads(raw)
    usage = obj.get("usage") or {}
    choice = (obj.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    completion_tokens = usage.get("completion_tokens") or 0
    return {
        "case": case["name"],
        "seconds": elapsed,
        "completion_tokens": completion_tokens,
        "prompt_tokens": usage.get("prompt_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "tokens_per_second": completion_tokens / elapsed if elapsed > 0 else 0,
        "finish_reason": choice.get("finish_reason"),
        "content_chars": len(msg.get("content") or ""),
        "reasoning_chars": len(msg.get("reasoning") or ""),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--output")
    args = parser.parse_args()

    rows = []
    for case in CASES:
        row = call(args.endpoint, args.model, case, args.temperature, args.seed, args.timeout)
        row["label"] = args.label
        rows.append(row)
        print(
            f"{row['case']:<20} {row['completion_tokens']:>5} tok "
            f"{row['seconds']:>7.2f}s {row['tokens_per_second']:>7.2f} tok/s "
            f"finish={row['finish_reason']}"
        )

    total_tokens = sum(r["completion_tokens"] for r in rows)
    total_seconds = sum(r["seconds"] for r in rows)
    summary = {
        "label": args.label,
        "cases": rows,
        "total_completion_tokens": total_tokens,
        "total_seconds": total_seconds,
        "aggregate_tokens_per_second": total_tokens / total_seconds if total_seconds > 0 else 0,
    }
    print(
        f"SUMMARY {args.label}: {total_tokens} tok in {total_seconds:.2f}s = "
        f"{summary['aggregate_tokens_per_second']:.2f} tok/s"
    )

    if args.output:
        with open(args.output, "w") as f:
            json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
