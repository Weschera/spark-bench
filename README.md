# spark-bench

A mixed-capability benchmark for evaluating LLMs on NVIDIA DGX Spark (GB10 Grace-Blackwell). 64 scenarios across 11 domains, with partial-credit grading, executable code tests, trial statistics, and visual artifact generation.

## Leaderboard (v4 — 64 scenarios, think-OFF, Q4_K_M)

Models are grouped by size tier. Within each tier, models compete against peers of similar capacity.

> **TrueScore v4 weights:** Quality 55%, Calibration 25%, Reliability 15%, Efficiency 1.5%, Responsiveness 3.5% (speed total: 5%)
>
> **v4** badge = current weights. **v1** badge = original weights (Quality 40%, Cal 25%, Rel 15%, Eff 5%, Resp 15%). Cross-version scores are not directly comparable.

### Small Tier (≤12B, single Spark)

| # | Model | TrueScore | Quality | Cal | Rel | Eff | Resp | Serving | Ver |
|---|-------|-----------|---------|-----|-----|-----|------|---------|-----|
| 1 | **Gemma 4 E4B** (4B dense) | **87.4** | 82.6 | 81.5 | 96.7 | 100.0 | 96.2 | llama.cpp, Q4_K_M | v1 |
| 2 | **Gemma 4 E2B** (2B dense) | **86.2** | 81.5 | 90.3 | 94.2 | 100.0 | 90.5 | llama.cpp, Q4_K_M | v4 |
| 3 | **Gemma 4 12B** (dense) | **85.0** | 79.9 | 86.9 | 98.8 | 100.0 | 87.4 | llama.cpp, Q4_K_M | v4 |

### Mid Tier (13–35B, single Spark)

| # | Model | TrueScore | Quality | Cal | Rel | Eff | Resp | Serving | Ver |
|---|-------|-----------|---------|-----|-----|-----|------|---------|-----|
| 1 | **Gemma 4 26B-A4B** (MoE) | **89.7** | 80.0 | 93.7 | 98.9 | 100.0 | 96.1 | llama.cpp, Q4_K_M | v1 |
| 2 | **Gemma 4 31B** (dense) | **87.7** | 80.9 | 95.3 | 99.8 | 100.0 | 82.3 | llama.cpp, Q4_K_M | v4 |
| 3 | **Ornith 1.0 35B** (MoE, 3B active) | **84.1** | 74.0 | 95.6 | 98.6 | 100.0 | 92.6 | llama.cpp, Q4_K_M | v4 |
| 4 | **AEON 7 Ultimate XS** (NVFP4, DFlash) | **79.9** | 78.4 | 61.6 | 95.6 | 100.0 | 91.7 | vLLM Docker, NVFP4 | v1 |
| 5 | **Qwopus 3.6-27B** v3 (MTP) | **68.1** | 61.4 | 82.1 | 93.1 | 12.2 | 56.2 | llama.cpp, Q4_K_M | v1 |
| 6 | **Huihui Qwen3.6-35B** (MoE) | **66.3** | 59.2 | 61.5 | 91.1 | 14.7 | 85.4 | llama.cpp, Q4_K_M | v1 |
| 7 | **Nemotron-3 Nano Omni** (30B) | **65.1** | 61.3 | 61.5 | 89.1 | 8.7 | 75.9 | llama.cpp, Q4_K_M | v1 |
| 8 | **HauhauCS Qwen3.6-35B** (MoE) | **60.7** | 52.5 | 52.6 | 90.4 | 10.0 | 83.3 | llama.cpp, Q4_K_M | v1 |
| 9 | **Bytkim Qwen3.6-27B** | **60.3** | 52.4 | 75.5 | 91.2 | 6.7 | 43.3 | llama.cpp, Q4_K_M | v1 |
| 10 | **Qwable-5-27B-Coder** | **58.8** | 46.6 | 79.7 | 87.7 | 7.6 | 44.4 | llama.cpp, Q4_K_M | v1 |
| 11 | **Qwen 3.6-27B base** | **53.4** | 48.9 | 66.4 | 82.7 | 6.0 | 30.4 | llama.cpp, Q4_K_M | v1 |

> Qwen 3.6-27B v4 benchmark in progress — will update when complete.

### Large Tier (2+ Sparks required)

| # | Model | TrueScore | Quality | Cal | Rel | Eff | Resp | Serving | Ver |
|---|-------|-----------|---------|-----|-----|-----|------|---------|-----|
| 1 | **DeepSeek V4 Flash** (MoE, dual-node) | **84.8** | 81.5 | 98.7 | 92.9 | 25.6 | 81.9 | vLLM, TP=2, RoCE | v1 |
| 2 | **GLM-5.2** (753B MoE) | **77.3** | 73.4 | 90.4 | 89.7 | 28.3 | 69.9 | OpenRouter API | v4 |

> GLM-5.2 scored via API. Local NVFP4 deployment (4× Spark) pending CRS812 switch (arriving June 28).
> Future Large-tier models: MiniMax-M3 (428B MoE), Nemotron-3 Ultra (550B).

## Serving Methods

| Model | Serving | Hardware |
|-------|---------|----------|
| Gemma 4 (all 5) | llama.cpp, Q4_K_M | Single DGX Spark |
| Ornith 35B | llama.cpp, Q4_K_M | Single DGX Spark |
| DeepSeek V4 Flash | vLLM, dual-node TP=2, RoCE | 2× DGX Spark |
| AEON 7 | vLLM Docker, NVFP4, DFlash n=10 | Single DGX Spark |
| GLM-5.2 | OpenRouter API | Remote (local NVFP4 planned) |
| All others | llama.cpp, Q4_K_M | Single DGX Spark |

## Deployment Recipes

- [Ornith 1.0-35B MoE](recipes/ornith-35b-moe.md) — Full deployment guide with benchmark results

## Benchmark Design

### 64 Scenarios · 11 Domains

| Domain | Scenarios | Description |
|--------|-----------|-------------|
| tool_use | 10 | Function calling with real tool schemas |
| instruction | 11 | Hard instruction following (constraints, format) |
| structured | 6 | JSON output with schema validation |
| long_context | 4 | Needle-in-haystack retrieval (8K-64K tokens) |
| safety | 11 | Refusal + appropriate compliance + over-refusal detection |
| robustness | 4 | Missing params, malformed input, injection |
| planning | 5 | Multi-step planning with tool orchestration |
| visual | 3 | Generate animated HTML5 canvas artifacts |
| code | 10 | Executable code generation (Python + SQL, graded by running) |
| composition | 2 | Multi-skill composition tasks |
| classification | 1 | Categorization with structured output |

### Grading

- **Partial credit** — a model hitting 3/5 constraints scores 0.60, not 0.00
- **Executable code tests** — model-generated Python/SQL is imported and run against test cases. Broken code fails. No pattern matching.
- **Pixel-based visual grading** — HTML artifacts rendered in headless Chromium, scored by pixel count, frame delta, and color diversity
- **Multi-turn tool calls** — graders check the full tool call sequence, not just the first response
- **Consistency score** — repeated trials must agree for full marks
- **Trial statistics** — Pass@1, Pass@K (all repeats pass), Reliability Gap, Score StdDev

### TrueScore v4 Formula

```
TrueScore = 0.55·Quality + 0.25·Calibration + 0.15·Reliability + 0.015·Efficiency + 0.035·Responsiveness
```

| Component | Weight | What it measures |
|-----------|--------|-----------------|
| Quality | 55% | Task correctness across all domains (including executable code) |
| Calibration | 25% | Safety + robustness (appropriate behavior, no over-refusal) |
| Reliability | 15% | Consistency across repeated trials |
| Efficiency | 1.5% | Tokens/second relative to fastest model |
| Responsiveness | 3.5% | Time-to-first-token + total latency |

> Speed components total 5% — quality dominates. This prevents fast-but-shallow models from outranking slower-but-smarter ones.

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
  --model model-name \
  --endpoint http://localhost:8000/v1 \
  --repeats 2 \
  --timeout 300

# Run with thinking enabled
python3 spark_bench.py eval \
  --label my-model-thinkon \
  --model model-name \
  --endpoint http://localhost:8000/v1 \
  --thinking on \
  --repeats 2
```

### Requirements

- Python 3.10+ (stdlib only — no pip dependencies)
- Any OpenAI-compatible `/v1/chat/completions` endpoint (llama.cpp, vLLM, OpenRouter, etc.)

## Repository Structure

```
spark-bench/
├── spark_bench.py          # Main benchmark harness
├── eval_suite.py           # 64 scenario definitions + graders
├── visual_pixel_grader.py  # Pixel-based visual artifact grader
├── html_report.py          # HTML report generator
├── recipes/                # Deployment + benchmark recipes
│   └── ornith-35b-moe.md   # Ornith 35B MoE deployment guide
├── results/
│   ├── spark_bench.csv     # All run data (long format, with mark + size_tier columns)
│   ├── runs/               # Per-run markdown + HTML reports
│   └── artifacts/          # Visual artifacts (HTML canvas animations)
└── README.md
```

## Hardware

Benchmarked on NVIDIA DGX Spark (GB10 Grace+Blackwell, 128GB unified memory):
- **Small/Mid tier**: served via llama.cpp with Q4_K_M quantization, one model per Spark
- **Large tier (DeepSeek V4 Flash)**: dual-node vLLM with RoCE interconnect
- **Large tier (GLM-5.2)**: OpenRouter API (local NVFP4 on 4× Spark pending CRS812 switch)
- **AEON 7**: vLLM Docker with NVFP4 quantization + DFlash speculative decoding

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgments

Benchmark methodology inspired by [tool-eval-bench](https://github.com/SeraphimSerapis/tool-eval-bench). Scenario design, grading, and code execution framework are custom-built for the DGX Spark deployment context.
