# Qwen3.6-27B NVIDIA NVFP4 + DFlash on 1× DGX Spark

Deploy NVIDIA's ModelOpt NVFP4 quantized Qwen3.6-27B with z-lab DFlash speculative decoding on a single DGX Spark. This recipe gives you 262K context, ~34 tok/s warm throughput, and ~3.4s median latency.

## Requirements

- 1× NVIDIA DGX Spark (128 GB unified memory)
- Docker with `--privileged` support
- HuggingFace access to `nvidia/Qwen3.6-27B-NVFP4` and `z-lab/Qwen3.6-27B-DFlash`

## Models

| Role | Model | Notes |
|---|---|---|
| Target (verifier) | `nvidia/Qwen3.6-27B-NVFP4` | Official NVIDIA ModelOpt NVFP4 checkpoint |
| Drafter (speculator) | `z-lab/Qwen3.6-27B-DFlash` | 5-layer DFlash drafter model (not MTP) |

> **DFlash ≠ MTP.** The NVFP4 checkpoint includes a built-in MTP head (`mtp_num_hidden_layers: 1`), but this recipe does **not** use it. DFlash is a separate 5-layer drafter (`DFlashDraftModel`) that reads intermediate hidden states from layers [1, 16, 31, 46, 61] of the target model to draft tokens. It's configured via `--speculative-config '{"method":"dflash",...}'`.

## Container

```
vllm/vllm-openai:nightly-aarch64-nccl230
```

Use the spark-vllm-docker launcher (see [recipes/README.md](../spark-vllm-docker/recipes/README.md)) or run directly with Docker.

## Quick start

If you have the spark-vllm-docker repo set up:

```bash
cd spark-vllm-docker
./run-recipe.sh qwen3.6-27b-nvidia-nvfp4-dflash --solo --setup
```

`--setup` builds the container (if missing), downloads both models (if missing), and launches vLLM.

To run without the recipe wrapper, use the vLLM command directly:

```bash
vllm serve nvidia/Qwen3.6-27B-NVFP4 \
  --served-model-name qwen36-27b-nvidia-nvfp4-dflash \
  --host 0.0.0.0 \
  --port 8000 \
  --tensor-parallel-size 1 \
  --trust-remote-code \
  --quantization modelopt \
  --attention-backend flash_attn \
  --kv-cache-dtype bfloat16 \
  --gpu-memory-utilization 0.84 \
  --max-model-len 262144 \
  --max-num-seqs 4 \
  --max-num-batched-tokens 32768 \
  --enable-chunked-prefill \
  --enable-prefix-caching \
  --language-model-only \
  --skip-mm-profiling \
  --reasoning-parser qwen3 \
  --tool-call-parser qwen3_xml \
  --enable-auto-tool-choice \
  --generation-config vllm \
  --speculative-config '{"method":"dflash","model":"z-lab/Qwen3.6-27B-DFlash","num_speculative_tokens":10}'
```

## Key flags explained

| Flag | Why |
|---|---|
| `--quantization modelopt` | Loads the NVFP4 checkpoint through NVIDIA's ModelOpt runtime |
| `--attention-backend flash_attn` | FlashAttention 2 — fastest attention kernel on GB10 |
| `--kv-cache-dtype bfloat16` | BF16 KV cache; preserves quality at 262K context |
| `--gpu-memory-utilization 0.84` | Tuned to leave headroom for the DFlash drafter model |
| `--max-num-seqs 4` | Low concurrency — this is a 27B model on one Spark |
| `--max-num-batched-tokens 32768` | Large batch for chunked prefill throughput |
| `--language-model-only` | Skip vision/multimodal components, save memory |
| `--speculative-config` | DFlash with `num_speculative_tokens=10` — the tuned sweet spot |
| `--reasoning-parser qwen3` | Parses `<think>` tags for thinking mode |
| `--tool-call-parser qwen3_xml` | XML-style tool call parsing |

> **Compile/CUDA graphs:** This recipe does NOT pass `--enforce-eager`, which means vLLM compile and CUDA graph capture are enabled. This adds ~100s to startup (308s vs 201s for eager) but improves warm runtime throughput by ~7%.

## DFlash tuning

The `num_speculative_tokens` (k) value was tuned with a fixed six-prompt probe:

| k | Compile | KV cache tokens | Max 262K concurrency | Warm tok/s | Notes |
|---:|---|---:|---:|---:|---|
| 15 | no | 666,993 | 2.54× | 30.8 | Baseline; lower acceptance |
| 8 | no | 704,668 | 2.69× | 29.4 | Higher acceptance %, lower throughput |
| 12 | no | 679,557 | 2.59× | 29.3 | Did not beat k=15 |
| 10 | no | 711,399 | 2.71× | 32.1 | Best eager candidate |
| **10** | **yes** | **668,545** | **2.55×** | **34.4** | **Final recipe — fastest** |

**Takeaway:** Don't optimize for DFlash acceptance percentage alone. Lower k improves acceptance % but can reduce useful draft throughput. k=10 with compile enabled was the clear winner on end-to-end throughput.

## Environment variables

```bash
VLLM_FLOAT32_MATMUL_PRECISION=high
```

## Recipe YAML

The full recipe file for spark-vllm-docker is at:

```
spark-vllm-docker/recipes/qwen3.6-27b-nvidia-nvfp4-dflash.yaml
```

## Verify it's running

```bash
curl http://localhost:8000/v1/models
```

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen36-27b-nvidia-nvfp4-dflash",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 64
  }'
```

## Performance (Spark-Bench v5c)

| Metric | Value |
|---|---:|
| Median latency | 3.42s |
| Eval throughput | 52.3 tok/s |
| Warm probe throughput | 34.4 tok/s |
| KV cache (262K context) | 668,545 tokens |
| Max concurrency at 262K | 2.55× |
