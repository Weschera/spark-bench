# Qwen3.6-27B NVIDIA NVFP4 + DFlash on 1x DGX Spark

This is the exact optimized single-Spark recipe used for the Spark-Bench v5c run:

```text
Qwen3.6-27B-NVIDIA-NVFP4-DFlashCompileK10-vLLM-thinkOFF-64scen-v5c-1Spark-20260630-124527
```

## Result

| Metric | Value |
|---|---:|
| TrueScore | 81.0 |
| Capability | 75.1 |
| Operational | 89.8 |
| Quality | 75.1 |
| Calibration | 81.9 |
| Reliability | 97.8 |
| Efficiency | 100.0 |
| Responsiveness | 85.4 |
| Median latency | 3.42s |
| Output tokens | 28,305 |
| Eval output throughput | 52.3 tok/s |

Benchmark report:

```text
results/runs/Qwen3.6-27B-NVIDIA-NVFP4-DFlashCompileK10-vLLM-thinkOFF-64scen-v5c-1Spark-20260630-124527.md
results/runs/Qwen3.6-27B-NVIDIA-NVFP4-DFlashCompileK10-vLLM-thinkOFF-64scen-v5c-1Spark-20260630-124527.html
```

## Model

- Target: `nvidia/Qwen3.6-27B-NVFP4`
- DFlash drafter: `z-lab/Qwen3.6-27B-DFlash`
- Backend: `vllm/vllm-openai:nightly-aarch64-nccl230`
- Hardware: 1x NVIDIA DGX Spark
- Context: 262,144 tokens
- Thinking: disabled for benchmark and game prompts

## Serving recipe

The shareable Spark recipe is:

```text
/home/raulwesche/projects/spark-vllm-docker/recipes/qwen3.6-27b-nvidia-nvfp4-dflash.yaml
```

Final serving command:

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

Launch through `spark-vllm-docker`:

```bash
cd /home/raulwesche/projects/spark-vllm-docker
./run-recipe.sh qwen3.6-27b-nvidia-nvfp4-dflash -n 10.0.0.229 --name vllm_qwen36_27b_dflash
```

## Tuning sweep

All probes used the same fixed six-prompt mix and thinking disabled.

| Candidate | Context | Compile/CUDA graphs | KV cache | Max 262K concurrency | Warm probe tok/s | Notes |
|---|---:|---|---:|---:|---:|---|
| DFlash k=15 eager | 262K | no | 666,993 | 2.54x | 30.78 | Baseline recipe; lower average acceptance but decent draft throughput |
| DFlash k=8 eager | 262K | no | 704,668 | 2.69x | 29.37 | Higher acceptance percent, lower end-to-end throughput |
| DFlash k=12 eager | 262K | no | 679,557 | 2.59x | 29.25 | Did not beat k=15 |
| DFlash k=10 eager | 262K | no | 711,399 | 2.71x | 32.10 | Best eager candidate |
| DFlash k=10 compile | 262K | yes | 668,545 | 2.55x | 34.42 | Final recipe; slower cold start but fastest runtime |

Important tuning conclusion: optimizing only for DFlash acceptance percentage was misleading. Lower `num_speculative_tokens` improved average draft acceptance, but it also reduced useful draft throughput. The best measured recipe was `num_speculative_tokens=10` with vLLM compile/CUDA graphs enabled.

Startup tradeoff:

- k=10 eager engine init: about 201s after model load/profiling.
- k=10 compile engine init: about 308s after model load/profiling, with about 40s of torch compile.
- Compile mode reduced KV headroom versus k=10 eager, but preserved the full 262K configured context and improved warm single-stream throughput.

## Benchmark command

```bash
cd /home/raulwesche/projects/spark-bench
PYTHONUNBUFFERED=1 python3 -u spark_bench.py eval \
  --label "Qwen3.6-27B-NVIDIA-NVFP4-DFlashCompileK10-vLLM-thinkOFF-64scen-v5c-1Spark" \
  --endpoint http://127.0.0.1:8000/v1 \
  --model qwen36-27b-nvidia-nvfp4-dflash \
  --thinking off \
  --repeats 2 \
  --tier all \
  --gen-tokens 256 \
  --timeout 600 \
  --topology "1x DGX Spark" \
  --parallelism 1 \
  --spec-decode dflash-k10-compile \
  --notes "nvidia/Qwen3.6-27B-NVFP4 with z-lab/Qwen3.6-27B-DFlash, vLLM nightly aarch64, ModelOpt NVFP4, TP1, max_model_len=262144, gpu_memory_utilization=0.84, max_num_batched_tokens=32768, max_num_seqs=4, num_speculative_tokens=10, compile/CUDA graphs enabled."
```

## Game artifacts

Generated after the benchmark using raw model output. No manual gameplay fixes were applied.

| Game | Max tokens | Completion tokens | Elapsed | Website path |
|---|---:|---:|---:|---|
| Frogger | 12,000 | 5,980 | 143.1s | `/dgx/animations/qwen36-27b-nvidia-dflash-k10-frogger-v5c.html` |
| Space Invaders | 8,000 | 4,478 | 95.4s | `/spaceinvaders/qwen36-27b-nvidia-dflash-k10.html` |

Raw artifact source:

```text
results/artifacts/Qwen3.6-27B-NVIDIA-NVFP4-DFlashCompileK10-vLLM-thinkOFF-64scen-v5c-1Spark-20260630-124527/FROGGER.html
results/artifacts/Qwen3.6-27B-NVIDIA-NVFP4-DFlashCompileK10-vLLM-thinkOFF-64scen-v5c-1Spark-20260630-124527/SPACE-INVADERS.html
```
