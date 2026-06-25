# spark-bench

A mixed-capability benchmark for evaluating LLMs on local deployment hardware (NVIDIA DGX Spark / GB10). 57 scenarios across 10 domains, with partial-credit grading, trial statistics, and visual artifact generation.

## Results

| Model | TrueScore | Quality | Calibration | Reliability | Efficiency | Responsiveness | Pass@1 | Pass@K | RelGap |
|-------|-----------|---------|-------------|-------------|------------|----------------|--------|--------|--------|
| **GLM-5.2** (OpenRouter) | **77.1** | 67.3 | 85.0 | 93.0 | 29.0 | 77.0 | 84.2% | 77.2% | 7.0% |
| **Qwopus 3.6-27B v2** (Q4_K_M, MTP) | **68.1** | 61.0 | 82.0 | 93.0 | 12.0 | 56.0 | 75.4% | 70.2% | 5.3% |
| **Qwen 3.6-27B base** (Q4_K_M) | **53.4** | 49.0 | 66.0 | 83.0 | 6.0 | 30.0 | 66.7% | 47.4% | 19.3% |

> **TrueScore weights:** Quality 50%, Reliability 20%, Efficiency 10%, Responsiveness 20%.
> Safety scenarios excluded from scoring (shown as notes only — uncensored models shouldn't be penalized).

### Visual Artifacts

Each model generates self-contained HTML5 canvas animations (no external libraries). The VIS-01 scenario asks for an animated solar system with 6+ orbiting planets.

| Model | VIS-01 (Solar System) | VIS-02 (Spiral Galaxy) | VIS-03 (DNA Helix) |
|-------|----------------------|----------------------|-------------------|
| GLM-5.2 | 1.00 | 0.83 | 1.00 |
| Qwopus | 0.63 | 0.83 | 0.63 |
| Qwen base | 1.00 | 0.83 | 0.63 |

## Benchmark Design

### 57 Scenarios · 10 Domains

| Domain | Scenarios | Description |
|--------|-----------|-------------|
| tool_use | 8 | Function calling with real tool schemas |
| instruction | 6 | Hard instruction following (constraints, format) |
| structured | 5 | JSON output with schema validation |
| long_context | 6 | Needle-in-haystack retrieval (8K-64K tokens) |
| safety | 4 | Refusal + appropriate compliance |
| robustness | 4 | Missing params, malformed input, injection |
| multi_step_chain | 3 | Sequential tool calls with dependencies |
| restraint_refusal | 4 | Over-refusal detection (should comply) |
| autonomous_planning | 2 | Multi-step planning with tool orchestration |
| visual | 3 | Generate animated HTML5 canvas artifacts |

### Grading

- **Partial credit** — a model hitting 3/5 constraints scores 0.60, not 0.00
- **Multi-turn tool calls** — graders check the full tool call sequence, not just the first response
- **Consistency score** — repeated trials must agree for full marks
- **Trial statistics** — Pass@1, Pass@K (all repeats pass), Reliability Gap, Score StdDev

### Scoring

| Component | Weight | What it measures |
|-----------|--------|-----------------|
| Quality | 50% | Task correctness across all domains |
| Reliability | 20% | Consistency across repeated trials |
| Efficiency | 10% | Tokens/second relative to fastest model |
| Responsiveness | 20% | Time-to-first-token + total latency |

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

# Filter by domain
python3 spark_bench.py eval \
  --label my-model-tools \
  --model model-name \
  --endpoint http://localhost:8000/v1 \
  --domains tool_use,multi_step_chain
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
├── results/
│   ├── spark_bench.csv     # All run data (long format)
│   ├── runs/               # Per-run markdown + HTML reports
│   └── artifacts/          # Visual artifacts (HTML canvas animations)
└── README.md
```

## Hardware

Benchmarked on NVIDIA DGX Spark (GB10 Grace+Blackwell, 128GB unified memory):
- **Qwopus & Qwen base**: served via llama.cpp with Q4_K_M quantization
- **GLM-5.2**: served via OpenRouter API

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgments

Benchmark methodology inspired by [tool-eval-bench](https://github.com/miaAI-lab/tool-eval-bench). Scenario design and grading are custom-built for the DGX Spark deployment context.
