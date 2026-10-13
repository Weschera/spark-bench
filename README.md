# spark-bench

A mixed-capability benchmark for evaluating LLMs on **NVIDIA DGX Spark** (GB10 Grace-Blackwell), tuned for **agentic / Hermes-style** local serving: tool use, multi-turn workflows, executable code, and real cluster serving (vLLM, llama.cpp, multi-node).

**Current methodology: v7.0 Uncapped · 80 scenarios · 13 domains · 12 agentic workflows · 4 long-generation builds · 2 rendered 3D-animation scenarios**

**v7.0** adds a **long_gen** domain: LG-01 to LG-04 are long, machine-graded builds, including a spreadsheet engine with 40 hidden tests and an order ledger with 33 traces. It also folds in:
- the v6.8.1 coding hardening ([details](docs/coding-hardening-v6.8.1.md))
- the v6.8.2 agentic hardening ([details](docs/agentic-hardening-v6.8.2.md))
- the v6.8.3 long-context reconciliation ([details](docs/long-context-hardening-v6.8.3.md))

**Runner changes:**
- Repeats get distinct seeds (`SPARK_BENCH_SEED_PER_REPEAT`).
- One temperature can be forced across every scenario for model-recommended sampling (`SPARK_BENCH_FORCE_TEMPERATURE`).
- Uncapped runs send the remaining context window as `max_tokens` (`SPARK_BENCH_CONTEXT`), because some engines default to 4,096 when it's omitted.
- The uncapped budget accounts for tool-call history.

v7.0 scores are not comparable with v6.x.

| | |
|---|---|
| Scenarios | **80** (base + hard + expert agentic + long_gen) |
| Domains | **13** |
| Agentic | **12** multi-turn workflows (AG-01…AG-12), including deep chains, tool failure injection, nested schemas, long noisy context |
| TrueScore weights | Quality 55% · Calibration 25% · Reliability 15% · Efficiency 1.5% · Responsiveness 3.5% (speed total **5%**) |
| Integrity | Golden-gate grader self-test, endpoint model + tool-call preflight, grader git provenance, one-eval-per-box lock, run heartbeats |
| Output | Long-format CSV (`results/spark_bench.csv`) + per-run markdown/HTML/JSON transcripts; current qualified board at [wesche.com/dgx](https://wesche.com/dgx) |

> **Scope:** This is a **DGX Spark operator bench**, not a universal LMSYS-style ranking. It answers: *which model + recipe should I serve on this cluster for agentic / Hermes work?*

---

## Leaderboard

### Latest: v7.0 ladder (October 12, 2026)

33 valid full runs: local deployments on DGX Sparks and a Mac Studio, plus the free models on Nous Portal. 80 scenarios, 2 repeats, uncapped, card sampling. Full tables with quant, engine, recipe and score components: [`results/comparisons/2026-10-12-v7-ladder`](results/comparisons/2026-10-12-v7-ladder/README.md).

**Thinking ON**

| # | Deployment | Hardware | TrueScore |
|---:|---|---|---:|
| 1 | missingno (stealth model, Nous Portal free API, thinking always on) | hosted | **91.2** |
| 2 | GLM-5.3-Flash EXL3 4bpw, TensorFold + DFlash2 | 2 Sparks TP2 | **88.9** |
| 3 | DeepSeek-V4.1-Flash EXL3 2.9bpw, vLLM + DSpark | 2 Sparks TP2 | **88.7** |
| 4 | RED-SNOW-5.3-Flash EXL3 4.91bpw, TensorFold + DFlash2 (unclosed-think fix) | 2 Sparks TP2 | **87.7** |
| 5 | Step 5 preview (Nous Portal free API, thinking always on) | hosted | **84.2** |

**Thinking OFF (top 10 of 28)**

| # | Deployment | Hardware | TrueScore |
|---:|---|---|---:|
| 1 | Nemotron-3-Ultra 550B NVFP4, SGLang TP4+EP4 | 4 Sparks TP4 | **90.0** |
| 2 | DeepSeek-V4.1-Flash EXL3 2.9bpw, vLLM + DSpark | 2 Sparks TP2 | **89.5** |
| 3 | RED-SNOW-5.3-Flash EXL3 4.91bpw, TensorFold + DFlash2 | 2 Sparks TP2 | **87.0** |
| 4 | Qwen3.8-27B BF16, mlx-lm | Mac Studio | **86.7** |
| 5 | RED-SNOW-5.3-Flash EXL3 2.49bpw, exllamav3 + MTP | 1 Spark | **85.1** |
| 6 | GLM-5.3-Flash EXL3 4bpw, TensorFold + DFlash2 | 2 Sparks TP2 | **84.8** |
| 7 | Qwen3.8-27B MLX 8-bit, TensorFold + DFlash2 | Mac Studio | **84.7** |
| 8 | Laguna XS 2.1 (Nous Portal free API) | hosted | **84.6** |
| 9 | Ling 3.1 Flash (Nous Portal free API) | hosted | **84.5** |
| 10 | GLM-5.3 (full) EXL3 3.38bpw, TensorFold + DFlash2 | 4 Sparks TP4 | **84.4** |

Rows are deployments, not models; gaps under about 1 point are noise. Hosted rows are ranked on quality only (their latency includes the internet). The first six-run v7.0 cohort is still in [`results/comparisons/2026-10-07-v7-cohort`](results/comparisons/2026-10-07-v7-cohort/README.md).

### Previous: v6.8.0 uncapped comparison

**Qwen3.8-Flash-Next spec-off scored 87.02 vs GLM-5.3-Flash DFlash2 K7 at
85.67** across the full 76-scenario, two-repeat contract. The audited package,
including all per-repeat scores, corrected context-length failures, transcript
hashes, and the excluded Qwen NEXTN A/B, is at
[`results/comparisons/2026-08-29-qwen38-flash-next-vs-glm53-flash-v680`](results/comparisons/2026-08-29-qwen38-flash-next-vs-glm53-flash-v680/README.md).

**The live leaderboard** ([wesche.com/dgx](https://wesche.com/dgx)) shows only
the 29 qualified runs from the current one-Spark `v6.7.1-challenge` cohort.
The complete 40-attempt evidence pack, including quarantine and preflight
failures, is in
[`results/cohorts/2026-08-01-one-spark-v671`](results/cohorts/2026-08-01-one-spark-v671/README.md).
The master `results/spark_bench.csv` retains older runs for provenance, but
scores from different methodology versions are not comparable.

### Current one-Spark cohort

| # | Deployment | TrueScore | Quality | Calibration | Reliability |
|---:|---|---:|---:|---:|---:|
| 1 | DeepSeek V4 Flash 0731, DS4 spec-off | **92.0** | 93.8 | 92.7 | 86.8 |
| 2 | DeepSeek V4 Flash 0731, DSpark | **86.7** | 88.7 | 87.1 | 79.6 |
| 3 | Qwopus AWQ, MTP K1 | **85.8** | 78.1 | 100.0 | 91.9 |
| 4 | Aeon Ultimate MM NVFP4, spec-off control | **85.3** | 82.7 | 93.7 | 83.8 |
| 5 | Gemma 4 26B-A4B Q4_K_M | **84.6** | 79.5 | 88.9 | 92.3 |

The full 29-row ranking is in
[`results-qualified.tsv`](results/cohorts/2026-08-01-one-spark-v671/results-qualified.tsv).
All rows use the same 20-scenario, 10-domain, three-repeat, thinking-off,
single-Spark TP1 contract at grader `11d21bf`.

Models are grouped by size tier. Within each tier, models compete against peers of similar capacity.

> **TrueScore weights (unchanged through v5c → v6.7.1):** Quality 55%, Calibration 25%, Reliability 15%, Efficiency 1.5%, Responsiveness 3.5% (speed total: 5%)
>
> **Calibration** measures prompt injection resistance, robustness, and over-refusal of legitimate requests. Content-refusal scenarios (harmful content requests) are **informational only — 0% weight** — because for uncensored models, answering everything is a feature.
>
> **Agentic (v6.7.1):** 12 multi-turn scenarios. Expert tier (AG-07…AG-12) adds dependency chains, injected tool failures, nested parameter schemas, and facts buried in long ops briefings. Graders check tool sequences **and** final-answer correctness.

### Historical snapshot — Small Tier (≤12B, single Spark) · v5c

| # | Model | TrueScore | Quality | Cal | Rel | Eff | Resp | Agentic | Serving |
|---|-------|-----------|---------|-----|-----|-----|------|---------|---------|
| 1 | **Gemma 4 E4B** (4B dense) | **75.9** | 60.9 | 94.0 | 94.9 | 100 | 91.7 | 3/36 ⭐ | llama.cpp, Q4_K_M |
| 2 | **Gemma 4 E2B** (2B dense) | **75.9** | 64.8 | 86.6 | 91.9 | 100 | 94.0 | 2/36 | llama.cpp, Q4_K_M |
| 3 | **Gemma 4 12B** (dense) | **74.9** | 63.8 | 81.9 | 98.6 | 100 | 86.5 | 1/36 | llama.cpp, Q4_K_M |

### Historical snapshot — Mid Tier (13–35B, single Spark) · v5c

| # | Model | TrueScore | Quality | Cal | Rel | Eff | Resp | Agentic | Serving |
|---|-------|-----------|---------|-----|-----|-----|------|---------|---------|
| 1 | **Qwopus 27B** (Qwen finetune) | **78.5** | 65.3 | 96.7 | 96.3 | 100 | 70.8 | 1/36 | llama.cpp, Q4_K_M |
| 2 | **Qwen 35B base** (MoE, 3B active) | **78.0** | 64.0 | 94.0 | 97.3 | 100 | 92.1 | 3/36 | llama.cpp, Q4_K_M |
| 3 | **Gemma 4 31B** (dense) | **77.4** | 64.3 | 93.5 | 99.6 | 100 | 64.5 | 1/36 | llama.cpp, Q4_K_M |
| 4 | **Nemotron 30B** (MoE, 3B active) | **76.0** | 59.9 | 94.0 | 99.0 | 100 | 91.7 | 2/36 | llama.cpp, Q4_K_M |
| 5 | **Bytkim 27B** (Qwen finetune) | **75.3** | 58.8 | 94.0 | 98.1 | 100 | 91.8 | 3/36 | llama.cpp, Q4_K_M |
| 6 | **Qwen 27B base** (dense) | **75.2** | 65.8 | 81.9 | 97.8 | 100 | 68.0 | 1/36 | llama.cpp, Q4_K_M |
| 7 | **Gemma 26B-A4B** (MoE, 4B active) | **75.2** | 59.5 | 94.0 | 95.2 | 100 | 91.3 | 2/36 | llama.cpp, Q4_K_M |
| 8 | **Huihui 35B** (MoE, abliterated) | **75.1** | 59.1 | 94.0 | 96.1 | 100 | 91.7 | 2/36 | llama.cpp, Q4_K_M |
| 9 | **Qwable 27B** (Coder finetune) | **74.3** | 64.3 | 81.9 | 97.3 | 100 | 68.3 | 1/36 | llama.cpp, Q4_K_M |
| 10 | **Ornith 35B** (MoE, 3B active) | **73.4** | 58.2 | 88.2 | 97.3 | 100 | 91.4 | 2/36 | llama.cpp, Q4_K_M |
| 11 | **AEON 7** (NVFP4, DFlash) | **70.7** | 63.2 | 67.7 | 96.3 | 100 | 87.5 | 3/36 | vLLM Docker, NVFP4 |
| 12 | **HauhauCS 35B** (MoE, uncensored) | **68.9** | 65.3 | 54.3 | 97.8 | 100 | 93.2 | 2/36 | llama.cpp, Q4_K_M |

### Historical snapshot — Large Tier (2+ Sparks) · v5c

| # | Model | TrueScore | Quality | Cal | Rel | Eff | Resp | Agentic | Serving |
|---|-------|-----------|---------|-----|-----|-----|------|---------|---------|
| 1 | **DeepSeek V4 Flash** (MoE, dual-node) | **78.9** | 66.6 | 100.0 | 93.5 | 33.6 | 77.2 | 6/36 ⭐ | vLLM, TP=2, RoCE |

For current v6.x / NVFP4 / MTP / DFlash / multi-engine numbers, use the live board and `spark_bench.csv` (every row has a `run_id`).

---

## Methodology lineage (v5c → v6.8.0)

Building in public means admitting mistakes and correcting them:

### v6.8.0 Uncapped

- **No client completion cap.** `max_tokens` is omitted so reasoning and the
  final answer share only the server's advertised context ceiling.
- **No model-request timeout.** Full qualification runs use `--timeout 0`;
  infrastructure watchdogs remain separate from model scoring.
- **Native terminal validation.** `finish_reason=length` and detected runaway
  output are model failures worth zero, even if an earlier tool action or code
  fragment happened to satisfy part of a rubric.
- **Targeted degeneration guards.** Repeated-character and highly compressible
  repeated-phrase loops can be aborted without imposing a blanket output cap.
- **Exact tail recovery.** Scenario and repeat selectors allow interrupted runs
  to recover missing slots while preserving original evidence and run identity.

The 76-scenario bank and TrueScore weights are inherited unchanged from
v6.7.1. The generation and validation contract changed materially, so capped
v6.7.1 scores are not directly comparable to `v6.8.0-*-uncapped` results. See
[`docs/v680-uncapped.md`](docs/v680-uncapped.md).

### v5c
1. **6 agentic scenarios** — multi-turn workflows; models must chain tool calls.
2. **Calibration rewrite** — content refusal → informational (0% weight).
3. **Speed weight cut** to 5% so speed cannot wash out quality.
4. **One model per Spark** — multi-tenant GPU runs contaminated speed.
5. **Token tracking** + **serving throughput side sweep** (non-scoring `tier2` rows).

### v6.6 / v6.7 challenge → v6.7.1 (current)

- **Observed transcript audit repaired six scoring contracts.** CODE-12 now
  requests and verifies one portable per-instance lock; CODE-14's variadic
  signature now matches its executable tests; RO-03 accepts the observed valid
  abstention wording; RR-02 accepts the standard quoted tautology fixture;
  TUH-10 no longer offers two tools claiming the same live-city capability;
  and MSC-02 receives contact results before notification is graded.
- **PL-02 tool roles are explicit.** The stock tool returns one current company
  price, while web search supplies historical and broad-market performance.
- **Regression coverage uses the exact failed transcripts.** The repaired bank
  passes 40/40 unit tests, 17/17 grader self-tests, and the browser-rendered
  12/12 golden gate. See `docs/v671-contract-repair.md`.

Old v6.6 full-suite and v6.7 challenge scores remain historical evidence. They
must not be compared numerically with v6.7.1 reruns.

### v6.5 → v6.6

- **Seven identical-partial rubrics audited and repaired.** CODE-01, CODE-02,
  TUH-05, IFH-03, MSC-01, AP-02, and CODE-13 had prompt, fixture, protocol,
  or standard-library mock defects that produced the same partial score across
  GLM-5.2, Inkling Small, and DeepSeek V4 Flash 0731. The evidence and exact
  repair contract are in `docs/v65-identical-partials-audit.md`.
- **Structured output rebuilt for discrimination.** All five cases now test
  exact nested objects, discriminated unions, conditional fields, forbidden
  cross-variant fields, ordering, types, and adversarial decoys. The saturation
  evidence and verification boundary are in `docs/v66-discrimination-hardening.md`.
- **Safety rebuilt for calibration.** Eleven cases now mix legitimate dual-use
  compliance, proportionate actions, conditional restraint, subtle tool-result
  injection, over-refusal traps, and two informational harmful-content refusals.
- **Raw transcript persistence.** Every repeat now records messages, offered
  tools, response/reasoning, assembled tool calls, score, and grading reason.

Because prompts, fixtures, and graders changed, v6.6 scores are **not directly
comparable** to v6.5 scores. Models must be rerun under the new cohort.

### v6.4c → v6.5

- **VIS-04/VIS-05: rendered 3D narrative scenarios.** The v6.4c visual domain
  graded by static text proxies (canvas tag present, rAF present) — every
  competent model scored ~100 and the domain had zero discrimination. v6.5 adds
  two scenarios that are **rendered in headless Chromium and graded by pixels**:
  a two-car overtake (color-cluster centroid crossing must be observed on
  screen) and a stand→walk→run→stand locomotion cycle (smoothed
  motion-energy curve must show quiet→rise→peak→settle).
  three.js r160 is vendored (assets/) and served over loopback HTTP during
  grading (file:// silently blocks ES modules). Graders tolerate
  software-rendering slow-motion (adaptive capture with early exit, shape-based
  rather than wall-clock phase analysis, top-3-mean peaks so loop-reset impulse
  spikes can't fake a phase) and are golden-gated with 4 canned fixtures
  (layer 4). Calibration evidence: the same model produced a 1.00 artifact and
  a 0.32 artifact (GLM-5.2 local vs its cloud twin's unwatchable race framing)
  — the domain now discriminates craft. v6.5 scores are NOT comparable to
  v6.4c rows.

### v6.x → v6.4c
1. **v6.1** — Safety split: content refusal informational; security behaviour (injection, destructive-cmd refusal) scores as calibration. Reliability no longer gives 100% for consistent failure.
2. **v6.3** — Standard tool protocol in the agentic harness (`role:tool` + tool_calls retained).
3. **v6.4** — Expert agentic tier (AG-07…AG-12): deep dependency chains, deterministic tool failure injection + retry, nested schemas, long noisy context.
4. **v6.4b** — Structured domain no longer flat-1.0 (value + extra-key checks); agentic difficulty rebalanced.
5. **v6.4c** — Final-answer correctness gates on agentic; harder executable code (CODE-11…14); agentic efficiency bonus removed (it rewarded fast-but-wrong).
6. **Integrity gates** — golden-gate grader self-test, endpoint preflight (right model + parseable tool_calls), grader git provenance (dirty tree aborts), box locks, on-disk run markers (not `pgrep`).

New uncapped leaderboard rows stamp **v6.8.0-full-uncapped** or
**v6.8.0-challenge-uncapped**. Capped legacy rows retain **v6.7.1-full** or
**v6.7.1-challenge** so the comparability boundary remains explicit.

---

## Serving Methods

**Forward vLLM policy:** new vLLM-backed recipes should start from the newest validated stable vLLM at setup time (record image/wheel/tag/commit in the recipe). Existing leaderboard runs are **not** re-run for engine-only upgrades unless you intentionally rebenchmark.

See `recipes/` for published DGX Spark recipes (DeepSeek V4 Flash, Qwen NVFP4 + MTP/DFlash, Laguna XS, MiniMax, Step, etc.).

| Class | Typical serving | Hardware |
|-------|-----------------|----------|
| Large MoE / multi-node | vLLM, TP/PP, RoCE | 2–4× DGX Spark |
| NVFP4 + spec decode | vLLM (stock or forks), MTP / DFlash | 1–2× Spark |
| Dense / mid GGUF | llama.cpp, Q4_K_M | 1× Spark |

---

## Benchmark Design

### 76 Scenarios · 12 Domains (v6.7.1)

Counts from the live `eval_suite.SCENARIOS` bank:

| Domain | Scenarios | Description |
|--------|-----------|-------------|
| agentic | 12 | Multi-turn workflows (AG-01…AG-06 hard + AG-07…AG-12 expert) |
| code | 14 | Executable Python/SQL graded by running tests (incl. harder CODE-11…14) |
| safety | 11 | Dual-use/over-refusal calibration + 2 informational harmful-content refusals |
| instruction | 9 | Hard instruction following (constraints, format) |
| tool_use | 6 | Function calling with real tool schemas |
| planning | 5 | Multi-step planning with tool orchestration |
| structured | 5 | Exact nested/union JSON contracts with adversarial fields |
| robustness | 4 | Missing params, malformed input, injection |
| visual | 5 | Animated HTML5 canvas artifacts, including 2 rendered pixel-graded cases |
| long_context | 2 | Needle / retrieval under noise |
| composition | 2 | Multi-skill composition |
| classification | 1 | Categorization with structured output |

**Difficulty tiers:** `base` (18) · `hard` (52) · `expert` (6 agentic).

### Grading

- **Partial credit** — 3/5 constraints → 0.60, not 0.00
- **Executable code** — model Python/SQL run in a process sandbox against tests
- **Pixel-based visual grading** — HTML artifacts scored by render metrics
- **Multi-turn tool calls** — full tool sequence + env state, not first response only
- **Agentic harness** — multi-turn loop with simulated tools; expert scenarios inject failures and bury facts in long briefings; final-answer gates apply
- **Consistency** — repeated trials; reliability excludes all-error / never-pass rows
- **Trial stats** — Pass@1, Pass@K, Reliability Gap, score stddev
- **Run validity** — if >5% of scenarios are transport/timeout errors, the run is marked invalid

### TrueScore formula (v6.7.1)

```
TrueScore = 0.55·Quality + 0.25·Calibration + 0.15·Reliability + 0.015·Efficiency + 0.035·Responsiveness
```

| Component | Weight | What it measures |
|-----------|--------|-----------------|
| Quality | 55% | Task correctness (tools, code, agentic, instruction, structured, …) |
| Calibration | 25% | Injection resistance, robustness, security-relevant refusal / over-refusal (content refusal = 0%) |
| Reliability | 15% | Consistency across repeats (only non-error scenarios that pass at least once) |
| Efficiency | 1.5% | Useful-token ratio (answer vs answer+reasoning) — anti-overthink, **not** serving tok/s |
| Responsiveness | 3.5% | Latency-derived score from median scenario wall time |

> Speed-related components total **5%**. Quality dominates. Serving throughput (tok/s, concurrency, context sweep) is recorded separately as non-scoring **tier2** metrics under the same `run_id`.

### Size Tiers

| Tier | Range | Hardware | Rationale |
|------|-------|----------|-----------|
| Small | ≤12B params | 1× DGX Spark | Lightweight / edge |
| Mid | 13–35B params | 1× DGX Spark | Full single-node |
| Large | 36B+ or 2+ Sparks | 2–4× DGX Spark | Multi-node deployment |

### Integrity gates (run before scores count)

Every full `eval` (unless explicitly skipped for debug):

1. **Golden gate** — grader reproduces known scores on canned transcripts (`golden_gate.py`)
2. **Provenance** — grader git short hash; uncommitted grader files abort (or `--allow-dirty`)
3. **Preflight** — endpoint serves the requested model **and** emits parseable structured `tool_calls`
4. **Box lock** — one eval per endpoint host
5. **Run markers** — `.STARTED` / `.DONE` heartbeats (watchers must not use `pgrep` on job names)

---

## Usage

```bash
# Full graded eval against any OpenAI-compatible endpoint
python3 spark_bench.py eval \
  --label my-model-thinkoff \
  --endpoint http://localhost:8000/v1 \
  --model my-model \
  --thinking off --repeats 2 --temperature 0.3 --tier all \
  --uncapped --timeout 0 \
  --notes "clean run, single Spark, v6.8.0 uncapped"
```

Full eval runs automatically append the serving throughput sweep (`--throughput-contexts 1024,8192,32768`, concurrency `1,2,4,8`, gen tokens `512`). Use `--skip-throughput` only for quick/debug runs that should not be compared as full board rows.

Other entry points: `tier1` (RoCE interconnect), `tier2` (inference throughput), `tier3` (light workloads), `all` (tier2+tier3).

```bash
# Offline: prove the grader still works
python3 golden_gate.py
python3 eval_suite.py --selftest
```

---

## Hardware

- 4× NVIDIA DGX Spark (GB10 Grace-Blackwell, 128 GB unified memory each)
- Small/Mid: often llama.cpp (Q4_K_M) or single-node vLLM NVFP4 — **one model per Spark** for comparable speed
- Large: vLLM tensor/pipeline parallel across Sparks (RoCE)
- Pure stdlib Python for the core harness — no pip required for `spark_bench.py` / `eval_suite.py`

## Repository layout

| Path | Role |
|------|------|
| `spark_bench.py` | CLI harness (tier1/2/3 + `eval`) |
| `eval_suite.py` | Scenario bank + graders + TrueScore (v6.8.0 uncapped; capped legacy stamps retained) |
| `golden_gate.py` | Offline grader self-check |
| `html_report.py` / `render_leaderboard.py` | Per-run HTML + board render |
| `visual_pixel_grader.py` | Visual domain grading helper |
| `recipes/` | Published serve recipes for DGX Spark |
| `tests/` | Mock OpenAI server for gate tests |
| `results/spark_bench.csv` | Long-format score source of truth |
| `results/runs/` | Per-run markdown/HTML + markers |
| `results/artifacts/` | Generated code/visual artifacts |
| `archive/` | One-off drivers, probes, lab scripts (not needed for a normal eval) — see `archive/README.md` |

---

## License

MIT licensed. Methodology inspired by [tool-eval-bench](https://github.com/miaAI-lab/tool-eval-bench).

Live leaderboard: [wesche.com/dgx](https://wesche.com/dgx)
