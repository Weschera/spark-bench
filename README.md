# spark-bench

A mixed-capability benchmark for evaluating LLMs on NVIDIA DGX Spark (GB10 Grace-Blackwell). 64 scenarios across 11 domains, with 6 agentic multi-turn workflows, partial-credit grading, executable code tests, trial statistics, and visual artifact generation.

## Leaderboard (v5c — 64 scenarios, think-OFF, Q4_K_M)

Models are grouped by size tier. Within each tier, models compete against peers of similar capacity.

> **TrueScore v5c weights:** Quality 55%, Calibration 25%, Reliability 15%, Efficiency 1.5%, Responsiveness 3.5% (speed total: 5%)
>
> **Calibration** measures prompt injection resistance, robustness, and over-refusal detection. Content-refusal scenarios (harmful content requests) are informational only — 0% weight — because for uncensored models, answering everything is a feature.
>
> **Agentic** = multi-step workflow checks passed (out of 36 total across 6 scenarios). Models must chain 8-20 tool calls to complete real tasks.

### Small Tier (≤12B, single Spark)

| # | Model | TrueScore | Quality | Cal | Rel | Eff | Resp | Agentic | Serving |
|---|-------|-----------|---------|-----|-----|-----|------|---------|---------|
| 1 | **Gemma 4 E4B** (4B dense) | **75.9** | 60.9 | 94.0 | 94.9 | 100 | 91.7 | 3/36 ⭐ | llama.cpp, Q4_K_M |
| 2 | **Gemma 4 E2B** (2B dense) | **75.9** | 64.8 | 86.6 | 91.9 | 100 | 94.0 | 2/36 | llama.cpp, Q4_K_M |
| 3 | **Gemma 4 12B** (dense) | **74.9** | 63.8 | 81.9 | 98.6 | 100 | 86.5 | 1/36 | llama.cpp, Q4_K_M |

> E4B (4B) has the best agentic score of any single-Spark model — small enough to be fast, smart enough to chain 2-3 tool calls.

### Mid Tier (13–35B, single Spark)

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

> Qwen 27B base has the highest raw Quality (65.8) in mid-tier but drops to #6 on calibration (over-refuses legitimate "kill process" requests, hallucinates through irrelevant text instead of abstaining). Qwen 35B base fixes both issues and jumps to #2.

### Large Tier (2+ Sparks required)

| # | Model | TrueScore | Quality | Cal | Rel | Eff | Resp | Agentic | Serving |
|---|-------|-----------|---------|-----|-----|-----|------|---------|---------|
| 1 | **DeepSeek V4 Flash** (MoE, dual-node) | **78.9** | 66.6 | 100.0 | 93.5 | 33.6 | 77.2 | 6/36 ⭐ | vLLM, TP=2, RoCE |

> DeepSeek V4 Flash is the only model that reliably completes multi-turn agentic workflows (6/36 checks). Perfect calibration (100). Dual-node TP=2 on 2× DGX Spark via RoCE. Efficiency is low (33.6) because dual-node inference is slower per-token, but speed is only 5% of TrueScore.
>
> Future Large-tier models (pending CRS812 switch): GLM-5.2 (753B MoE, NVFP4), MiniMax-M3 (428B MoE), Nemotron-3 Ultra (550B).

## What changed in v5c

Building in public means admitting mistakes and correcting them:

1. **Added 6 agentic scenarios** — multi-turn workflows replacing 6 trivial perfect-score scenarios. Models must chain tool calls across 8-20 steps. First version that tests whether a model can actually *do* things, not just answer questions.

2. **Revised calibration scoring** — content-refusal scenarios (harmful content requests) moved to informational group with 0% weight. For uncensored/abliterated models, answering everything is a feature. Calibration still penalizes prompt injection, tool fabrication, and over-refusal of legitimate requests.

3. **Speed weight reduced** from 20% (v1) to 5% — speed was masking model intelligence. Nemotron jumped from 65.1 → 76.0, Bytkim from 60.3 → 75.3.

4. **One model per Spark** — running multiple models on the same GPU contaminated speed scores. All affected runs killed and re-run clean.

5. **Token tracking** — output tokens per scenario and total per run added as non-scoring side stat.

6. **Serving throughput side sweep** — every full v5c `eval` now also records single-stream decode tok/s at 1K/8K/32K context and aggregate decode tok/s at concurrency 1/2/4/8. These are non-scoring side stats stored as `tier2` rows under the same run id.

## Serving Methods

**Forward vLLM policy:** new vLLM-backed benchmark recipes should start from the newest validated stable vLLM available at setup time (v0.24.0 as of 2026-07-01), unless a model-specific recipe requires a pinned fork or container. Record the exact image, wheel, tag, or commit in the recipe notes. Existing leaderboard runs are not rerun for engine-only upgrades; they stay historical unless the model or serving recipe is intentionally rebenchmarked.

| Model | Serving | Hardware |
|-------|---------|----------|
| DeepSeek V4 Flash | vLLM, dual-node TP=2, RoCE | 2× DGX Spark |
| AEON 7 | vLLM Docker, NVFP4, DFlash n=10 | Single DGX Spark |
| All others | llama.cpp, Q4_K_M | Single DGX Spark |

## Benchmark Design

### 64 Scenarios · 11 Domains

| Domain | Scenarios | Description |
|--------|-----------|-------------|
| agentic | 6 | Multi-turn workflows (8-20 tool calls per scenario) |
| tool_use | 10 | Function calling with real tool schemas |
| instruction | 11 | Hard instruction following (constraints, format) |
| code | 10 | Executable Python + SQL (graded by running) |
| safety | 11 | Refusal + appropriate compliance + over-refusal |
| structured | 6 | JSON output with schema validation |
| long_context | 4 | Needle-in-haystack retrieval (8K-64K tokens) |
| robustness | 4 | Missing params, malformed input, injection |
| planning | 5 | Multi-step planning with tool orchestration |
| visual | 3 | Generate animated HTML5 canvas artifacts |
| composition | 2 | Multi-skill composition tasks |
| classification | 1 | Categorization with structured output |

### Grading

- **Partial credit** — a model hitting 3/5 constraints scores 0.60, not 0.00
- **Executable code tests** — model-generated Python/SQL is imported and run against test cases. Broken code fails. No pattern matching.
- **Pixel-based visual grading** — HTML artifacts rendered in headless Chromium, scored by pixel count, frame delta, and color diversity
- **Multi-turn tool calls** — graders check the full tool call sequence, not just the first response
- **Agentic harness** — system prompt + continuation cue, max 20 turns per scenario. Graded by which workflow steps were completed.
- **Consistency score** — repeated trials must agree for full marks
- **Trial statistics** — Pass@1, Pass@K (all repeats pass), Reliability Gap, Score StdDev

### TrueScore v5c Formula

```
TrueScore = 0.55·Quality + 0.25·Calibration + 0.15·Reliability + 0.015·Efficiency + 0.035·Responsiveness
```

| Component | Weight | What it measures |
|-----------|--------|-----------------|
| Quality | 55% | Task correctness across all domains (including executable code + agentic) |
| Calibration | 25% | Prompt injection resistance, robustness, over-refusal (content refusal = 0% weight) |
| Reliability | 15% | Consistency across repeated trials |
| Efficiency | 1.5% | Tokens/second relative to fastest model |
| Responsiveness | 3.5% | Time-to-first-token + total latency |

> Speed components total 5% — quality dominates.

### Size Tiers

| Tier | Range | Hardware | Rationale |
|------|-------|----------|-----------|
| Small | ≤12B params | 1× DGX Spark | Lightweight models for edge/inference |
| Mid | 13–35B params | 1× DGX Spark | Full-capability single-node models |
| Large | 36B+ or 2+ Sparks | 2–4× DGX Spark | Multi-node deployment required |

## Usage

```bash
# Run against any OpenAI-compatible endpoint
python3 spark_bench.py eval \
  --label my-model-thinkoff \
  --endpoint http://localhost:8000/v1 \
  --model my-model.gguf \
  --thinking off --repeats 2 --temperature 0.3 --tier all \
  --notes "clean run, single Spark"
```

Full v5c eval runs automatically append the serving throughput sweep using `--throughput-contexts 1024,8192,32768`, `--throughput-concurrency 1,2,4,8`, and `--throughput-gen-tokens 512`. Use `--skip-throughput` only for quick/debug runs that should not be comparable.

## Hardware

- 4× NVIDIA DGX Spark (GB10 Grace-Blackwell, 128 GB unified memory each)
- Small/Mid tier: llama.cpp (Q4_K_M), one model per Spark
- Large tier: vLLM with tensor parallelism across multiple Sparks (RoCE interconnect)
- Pure stdlib Python — no pip dependencies

## License

MIT licensed. Methodology inspired by [tool-eval-bench](https://github.com/miaAI-lab/tool-eval-bench).

Live leaderboard: [wesche.com/dgx](https://wesche.com/dgx)
