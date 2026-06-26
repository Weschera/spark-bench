# spark-bench

A mixed-capability benchmark for evaluating LLMs on local deployment hardware (NVIDIA DGX Spark / GB10). 57 scenarios across 10 domains, with partial-credit grading, trial statistics, and visual artifact generation.

## Leaderboard (v2 — 57 scenarios, think-OFF, Q4_K_M)

| # | Model | TrueScore | Quality | Cal | Rel | Eff | Resp | Pass@1 | Pass@K | RelGap | Latency | Tool-Eval |
|---|-------|-----------|---------|-----|-----|-----|------|--------|--------|--------|---------|-----------|
| 1 | **Gemma 4 26B-A4B** (MoE) | **89.7** | 80.0 | 93.7 | 98.9 | 100.0 | 96.1 | 89.5% | 87.7% | 1.8% | 0.8s | — |
| 2 | **Gemma 4 31B** (dense) | **89.2** | 81.8 | 95.3 | 100.0 | 100.0 | 84.4 | 89.5% | 89.5% | 0.0% | 3.7s | — |
| 3 | **Gemma 4 E2B** (dense) | **88.7** | 82.4 | 84.9 | 98.8 | 100.0 | 98.2 | 89.5% | 89.5% | 0.0% | 0.4s | — |
| 4 | **Ornith 1.0 35B** (MoE) | **87.5** | 75.3 | 95.6 | 94.9 | 100.0 | 94.8 | 91.2% | 82.5% | 8.8% | 1.1s | 84 |
| 5 | **Gemma 4 12B** (dense) | **87.4** | 79.8 | 86.9 | 99.8 | 100.0 | 92.0 | 87.7% | 87.7% | 0.0% | 1.8s | 92 |
| 6 | **Gemma 4 E4B** (dense) | **87.4** | 82.6 | 81.5 | 96.7 | 100.0 | 96.2 | 87.7% | 86.0% | 1.8% | 0.8s | — |
| 7 | **DeepSeek V4 Flash** (MoE, dual-node) | **84.8** | 81.5 | 98.7 | 92.9 | 25.6 | 81.9 | 94.7% | 89.5% | 5.3% | 4.4s | — |
| 8 | **AEON 7 Ultimate XS** (NVFP4, DFlash) | **79.9** | 78.4 | 61.6 | 95.6 | 100.0 | 91.7 | 82.5% | 77.2% | 5.3% | 1.8s | — |
| 9 | **GLM-5.2** (OpenRouter API) | **77.3** | 73.4 | 90.4 | 89.7 | 28.3 | 69.9 | 87.7% | 78.9% | 8.8% | 8.6s | — |
| 10 | **Qwopus 3.6-27B** v3 (MTP) | **68.1** | 61.4 | 82.1 | 93.1 | 12.2 | 56.2 | 75.4% | 70.2% | 5.3% | 15.6s | — |
| 11 | **Huihui Qwen3.6-35B** | **66.3** | 59.2 | 61.5 | 91.1 | 14.7 | 85.4 | 64.9% | 54.4% | 10.5% | 3.4s | — |
| 12 | **Nemotron-3-Nano-Omni-30B** | **65.1** | 61.3 | 61.5 | 89.1 | 8.7 | 75.9 | 73.7% | 61.4% | 12.3% | 6.4s | — |
| 13 | **HauhauCS Qwen3.6-35B** | **60.7** | 52.5 | 52.6 | 90.4 | 10.0 | 83.3 | 61.4% | 50.9% | 10.5% | 4.0s | — |
| 14 | **Bytkim Qwen3.6-27B** | **60.3** | 52.4 | 75.5 | 91.2 | 6.7 | 43.3 | 66.7% | 57.9% | 8.8% | 26.2s | — |
| 15 | **Qwable-5-27B-Coder** | **58.8** | 46.6 | 79.7 | 87.7 | 7.6 | 44.4 | 64.9% | 50.9% | 14.0% | 25.0s | — |
| 16 | **Qwen 3.6-27B base** | **53.4** | 48.9 | 66.4 | 82.7 | 6.0 | 30.4 | 66.7% | 47.4% | 19.3% | 45.8s | 89 |

> **TrueScore weights:** Quality 40%, Calibration 25%, Reliability 15%, Efficiency 5%, Responsiveness 15%.
> **Tool-Eval** column shows scores from [tool-eval-bench](https://github.com/SeraphimSerapis/tool-eval-bench) v2.0.7 (69 scenarios, independent benchmark) where available.
> All local models served via llama.cpp with Q4_K_M quantization unless otherwise noted.

### Serving Methods

| Model | Serving | Hardware |
|-------|---------|----------|
| Gemma 4 (all 5) | llama.cpp, Q4_K_M | Single DGX Spark |
| Ornith 35B | llama.cpp, Q4_K_M | Single DGX Spark |
| DeepSeek V4 Flash | vLLM, dual-node TP=2, RoCE | 2x DGX Spark |
| AEON 7 | vLLM Docker, NVFP4, DFlash n=10 | Single DGX Spark |
| GLM-5.2 | OpenRouter API | Remote |
| Qwopus | llama.cpp, Q4_K_M, MTP | Single DGX Spark |
| All others | llama.cpp, Q4_K_M | Single DGX Spark |

## Deployment Recipes

- [Ornith 1.0-35B MoE](recipes/ornith-35b-moe.md) — Full deployment guide with benchmark results

## Benchmark Design

### 57 Scenarios · 10 Domains

| Domain | Scenarios | Description |
|--------|-----------|-------------|
| tool_use | 10 | Function calling with real tool schemas |
| instruction | 11 | Hard instruction following (constraints, format) |
| structured | 6 | JSON output with schema validation |
| long_context | 4 | Needle-in-haystack retrieval (8K-64K tokens) |
| safety | 11 | Refusal + appropriate compliance |
| robustness | 4 | Missing params, malformed input, injection |
| planning | 5 | Multi-step planning with tool orchestration |
| visual | 3 | Generate animated HTML5 canvas artifacts |
| composition | 2 | Multi-skill composition tasks |
| classification | 1 | Categorization with structured output |

### Grading

- **Partial credit** — a model hitting 3/5 constraints scores 0.60, not 0.00
- **Multi-turn tool calls** — graders check the full tool call sequence, not just the first response
- **Consistency score** — repeated trials must agree for full marks
- **Trial statistics** — Pass@1, Pass@K (all repeats pass), Reliability Gap, Score StdDev

### Scoring

| Component | Weight | What it measures |
|-----------|--------|-----------------|
| Quality | 40% | Task correctness across all domains |
| Calibration | 25% | Safety + robustness (appropriate behavior) |
| Reliability | 15% | Consistency across repeated trials |
| Efficiency | 5% | Tokens/second relative to fastest model |
| Responsiveness | 15% | Time-to-first-token + total latency |

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
├── eval_suite.py           # 57 scenario definitions + graders
├── html_report.py          # HTML report generator
├── recipes/                # Deployment + benchmark recipes
│   └── ornith-35b-moe.md   # Ornith 35B MoE deployment guide
├── results/
│   ├── spark_bench.csv     # All run data (long format)
│   ├── runs/               # Per-run markdown + HTML reports
│   └── artifacts/          # Visual artifacts (HTML canvas animations)
└── README.md
```

## Hardware

Benchmarked on NVIDIA DGX Spark (GB10 Grace+Blackwell, 128GB unified memory):
- **Single-Spark models**: served via llama.cpp with Q4_K_M quantization
- **DeepSeek V4 Flash**: dual-node vLLM with RoCE interconnect
- **AEON 7**: vLLM Docker with NVFP4 quantization + DFlash speculative decoding
- **GLM-5.2**: OpenRouter API (remote)

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgments

Benchmark methodology inspired by [tool-eval-bench](https://github.com/SeraphimSerapis/tool-eval-bench). Scenario design and grading are custom-built for the DGX Spark deployment context.
