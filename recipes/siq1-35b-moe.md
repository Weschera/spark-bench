# SIQ-1-35B MoE — Deployment Guide

**Model:** SIQ-1-35B (AlexWortega/SIQ-1-35B on HuggingFace)  
**Architecture:** Qwen3_5MoeForCausalLM — hybrid linear-attention MoE (3 linear-attn : 1 full-attn, 256 experts, 3B active params)  
**Quantization:** Q4_K_M (≈20 GB)  
**Hardware tested:** NVIDIA RTX A6000 (46 GB), single GPU  

---

## Serving

```bash
# llama.cpp (mainline b8951+) — only backend that supports this arch
llama-server \
  -m SIQ-1-35B.Q4_K_M.gguf \
  -ngl 99 \
  -c 65536 \
  --host 0.0.0.0 \
  --port 8080 \
  --jinja \
  --flash-attn on \
  -np 1
```

> **Note:** vLLM and SGLang do **not** support `Qwen3_5MoeForCausalLM` (text-only arch). Only llama.cpp detects and serves it correctly via GGUF arch detection.

---

## Benchmark

```bash
python3 spark_bench.py eval \
  --label siq1-35b-thinkoff \
  --endpoint http://localhost:8080/v1 \
  --model SIQ-1-35B.Q4_K_M.gguf \
  --repeats 2 \
  --thinking off \
  --temperature 0.3 \
  --timeout 300
```

### Results

**Canonical (think-OFF, repeats=2, temp=0.3) — leaderboard run:**

| TrueScore | Quality | Cal | Rel | Eff | Resp | Pass@1 | Pass@K | RelGap | Latency |
|-----------|---------|-----|-----|-----|------|--------|--------|--------|---------|
| **87.3** | 79.2 | 88.6 | 93.0 | 100.0 | 96.8 | 91.2% | 86.0% | 5.3% | 0.65s |

Domain breakdown: instruction 89.9 · structured 89.2 · safety 97.4 · composition 100 · visual 95.1 · long_context 73.2 · planning 70.3 · tool_use 59.2

**Thinking-ON (effort=high, repeats=1) — extended reasoning mode:**

| TrueScore | Quality | Cal | Rel | Eff | Resp | Pass@1 | Latency |
|-----------|---------|-----|-----|-----|------|--------|---------|
| **76.2** | 66.7 | 81.4 | 100.0 | 13.3 | 90.1 | 71.9% | 2.21s |

Inject `Reasoning effort: High` as system message + `chat_template_kwargs: {enable_thinking: true}`. Thinking mode improves planning (+16) and structured output (+28) but kills efficiency score due to long reasoning traces.

---

## Model Notes

- **141 tok/s decode** on A6000 — fast due to MoE: only 3B active params per forward pass
- **4722 tok/s prefill** — linear-attention layers make long-context prefill very fast
- **Thinking mode** (`enable_thinking=true`) supported natively via llama.cpp Jinja template
- Native `tool_calls` in streaming responses (OpenAI-compatible)
- Context window: 65536 tokens (N_CTX served)
