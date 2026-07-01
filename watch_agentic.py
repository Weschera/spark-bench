#!/usr/bin/env python3
"""Watch spark_bench eval stdout log until all 6 agentic scenarios (AG-01..AG-06)
have printed their `[eval] AG-0N ... score=...` line, then print a summary
and exit so notify_on_complete pings Hex with the early agentic read."""
import os, re, time, sys

LOG = os.path.expanduser("~/projects/spark-bench/results/moa-3local-v5c.log")
AGENTIC = [f"AG-0{i}" for i in range(1, 7)]
# matches: "  [eval] AG-01  agentic        score=0.85 cons=0.90 (reason...)"
LINE_RE = re.compile(r"\[eval\]\s+(AG-0[1-6])\s+(\S+)\s+score=([0-9.]+)\s+cons=([0-9.]+)\s*\((.*)\)")

DEADLINE = time.time() + 4 * 3600  # 4h safety cap
seen = {}
last_emitted = -1

while time.time() < DEADLINE:
    try:
        with open(LOG) as f:
            text = f.read()
    except FileNotFoundError:
        text = ""
    for m in LINE_RE.finditer(text):
        sid, dom, score, cons, reason = m.groups()
        seen[sid] = (float(score), float(cons), reason.strip())
    if len(seen) != last_emitted:
        last_emitted = len(seen)
        print(f"[watch] {time.strftime('%H:%M:%S')} agentic completed: "
              f"{sorted(seen)} ({len(seen)}/6)", flush=True)
    if len(seen) >= 6:
        print("\n=== ALL 6 AGENTIC SCENARIOS COMPLETE (early read) ===", flush=True)
        scores = []
        for sid in AGENTIC:
            if sid in seen:
                sc, cons, reason = seen[sid]
                scores.append(sc)
                verdict = "PASS" if sc >= 0.5 else "FAIL"
                print(f"  {sid}: score={sc:.2f} cons={cons:.2f} [{verdict}]  {reason[:70]}", flush=True)
        if scores:
            mean = sum(scores) / len(scores)
            npass = sum(1 for s in scores if s >= 0.5)
            print(f"\n  AGENTIC MEAN score={mean:.2f}  |  passed {npass}/6", flush=True)
            if npass == 6:
                print("  VERDICT: MOA fix HELD — all agentic scenarios passed.", flush=True)
            elif npass >= 4:
                print("  VERDICT: mostly working — some agentic weakness.", flush=True)
            else:
                print("  VERDICT: agentic still struggling — investigate.", flush=True)
        sys.exit(0)
    time.sleep(20)

print(f"[watch] deadline reached; only {sorted(seen)} done ({len(seen)}/6)", flush=True)
sys.exit(2)
