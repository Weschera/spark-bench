# Deploying MiniMax-M3 NVFP4 on 4x DGX Spark

This is the exact 4-node MiniMax-M3 deployment used for the Spark-Bench v5c run:

```text
MiniMax-M3-NVFP4-vLLM-thinkOFF-64scen-v5c-4Spark-20260630-024756
```

Result: TrueScore **85.1**, median latency **5.45s**, **27,877** output tokens across 64 scenarios.

The working path uses the community NVIDIA forum recipe, not the official NVIDIA checkpoint path. The official checkpoint was tested first and produced runtime/backend failures on DGX Spark. The working setup is:

| Setting | Value |
|---------|-------|
| Model | `lukealonso/MiniMax-M3-NVFP4` |
| Container | `ghcr.io/tonyd2wild/vllm-m3-chthonic:nccl230u1` |
| Runtime | vLLM chthonic/B12X |
| Quantization | `modelopt_fp4` |
| Attention backend | `B12X_ATTN` |
| MoE backend | `b12x` |
| Parallelism | tensor parallel 4, no Ray |
| Context | 524,288 tokens |
| GPU memory utilization | 0.84 |
| Max sequences | 5 |
| Max batched tokens | 8192 |

The exact reusable YAML is stored next to this guide:

```text
recipes/minimax-m3-lukealonso-nvfp4.yaml
```

## Cluster

| Role | SSH IP | Hostname | Fabric IP |
|------|--------|----------|-----------|
| rank 0 / head | `10.0.0.109` | `spark-78f1` | `10.10.10.1` |
| rank 1 | `10.0.0.120` | `spark-b610` | `10.10.10.7` |
| rank 2 | `10.0.0.183` | `spark-366f` | `10.10.10.5` |
| rank 3 | `10.0.0.229` | `spark-9f73` | `10.10.10.3` |

Network flags used:

```bash
-n 10.10.10.1,10.10.10.7,10.10.10.5,10.10.10.3 \
  --eth-if enp1s0f0np0 \
  --ib-if rocep1s0f0 \
  --no-ray
```

## Prerequisites

Use `spark-vllm-docker` with `run-recipe.sh` available on the head node.

The model snapshot was downloaded and synced to all four nodes:

```text
~/.cache/huggingface/hub/models--lukealonso--MiniMax-M3-NVFP4/snapshots/e7c7b65dae74c25d44bf1f0670713d607f1beea9
```

Cache size per node was about 243 GB.

The working recipe expects NCCL 2.30.7 inside the container:

```text
/opt/nccl230/build/lib/libnccl.so.2
```

## Install the recipe

Copy the YAML into the 4-node recipe folder in `spark-vllm-docker`:

```bash
cp recipes/minimax-m3-lukealonso-nvfp4.yaml \
  /home/raulwesche/spark-vllm-docker/recipes/4x-spark-cluster/minimax-m3-lukealonso-nvfp4.yaml
```

## Launch

Run from the head node, or SSH to the head node from your workstation:

```bash
ssh 10.0.0.109 'export PATH=$HOME/.local/bin:$PATH; cd /home/raulwesche/spark-vllm-docker && PYTHONUNBUFFERED=1 ./run-recipe.sh recipes/4x-spark-cluster/minimax-m3-lukealonso-nvfp4.yaml -n 10.10.10.1,10.10.10.7,10.10.10.5,10.10.10.3 --eth-if enp1s0f0np0 --ib-if rocep1s0f0 --no-ray -d'
```

The API is served on:

```text
http://10.0.0.109:8000/v1
```

Served model name:

```text
minimax-m3
```

## Important flags

The recipe runs:

```bash
vllm serve lukealonso/MiniMax-M3-NVFP4 \
  --served-model-name minimax-m3 \
  --tensor-parallel-size 4 \
  --quantization modelopt_fp4 \
  --attention-backend B12X_ATTN \
  --moe-backend b12x \
  -cc.mode=VLLM_COMPILE \
  -cc.cudagraph_mode=FULL \
  --load-format safetensors \
  --kv-cache-dtype auto \
  --max-model-len 524288 \
  --max-num-batched-tokens 8192 \
  --max-num-seqs 5 \
  --gpu-memory-utilization 0.84 \
  --enable-chunked-prefill \
  --enable-prefix-caching \
  --skip-mm-profiling \
  --mm-encoder-tp-mode data \
  --block-size 128 \
  --generation-config vllm \
  --reasoning-parser minimax_m3 \
  --tool-call-parser minimax_m3 \
  --enable-auto-tool-choice
```

The YAML also installs `b12x==0.23.0`, forces the container to use NCCL 2.30.7, and applies compatibility patches for the installed B12X attention and MoE APIs.

## Environment

Key environment variables:

```bash
VLLM_NCCL_SO_PATH=/opt/nccl230/build/lib/libnccl.so.2
LD_PRELOAD=/opt/nccl230/build/lib/libnccl.so.2
NCCL_DEBUG=VERSION
NCCL_IB_DISABLE=0
NCCL_NET=ib
NCCL_NET_PLUGIN=none
NCCL_IB_HCA=rocep1s0f0,roceP2p1s0f0
NCCL_IB_GID_INDEX=3
NCCL_IB_MERGE_NICS=1
NCCL_IB_QPS_PER_CONNECTION=8
NCCL_IB_SPLIT_DATA_ON_QPS=1
NCCL_IB_PCI_RELAXED_ORDERING=1
NCCL_NET_GDR_LEVEL=LOC
NCCL_CUMEM_ENABLE=0
NCCL_IGNORE_CPU_AFFINITY=1
NCCL_ASYNC_ERROR_HANDLING=1
NCCL_SOCKET_IFNAME=enp1s0f0np0
GLOO_SOCKET_IFNAME=enp1s0f0np0
UCX_NET_DEVICES=enp1s0f0np0
VLLM_FLOAT32_MATMUL_PRECISION=high
```

## Successful startup markers

Expected log markers:

```text
Detected ModelOpt NVFP4 checkpoint
world_size=4
vLLM is using nccl==2.30.7
NCCL version 2.30.7+cuda13.2
Using AttentionBackendEnum.B12X_ATTN backend
Using 'B12X' NvFp4 MoE backend
FORCED_NCCL_VERSION 23007
Loading weights took about 635 seconds
Model loading took about 62 GiB memory
GPU KV cache size: 760,704 tokens
Maximum concurrency for 524,288 tokens per request: 1.45x
Application startup complete
```

Cold start was about 15 to 18 minutes.

## Verify

Health/model check:

```bash
curl -s http://10.0.0.109:8000/v1/models | python3 -m json.tool
```

Quick inference:

```bash
curl -s http://10.0.0.109:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "minimax-m3",
    "messages": [{"role": "user", "content": "What is 17 * 23? Answer with only the number."}],
    "max_tokens": 32,
    "temperature": 0
  }' | python3 -m json.tool
```

Expected answer: `391`.

## Benchmark command

```bash
cd /home/raulwesche/projects/spark-bench
PYTHONUNBUFFERED=1 python3 -u spark_bench.py eval \
  --label "MiniMax-M3-NVFP4-vLLM-thinkOFF-64scen-v5c-4Spark" \
  --endpoint http://10.0.0.109:8000/v1 \
  --model minimax-m3 \
  --thinking off \
  --repeats 2 \
  --tier all \
  --gen-tokens 256 \
  --timeout 600 \
  --notes "MiniMax-M3-NVFP4 (lukealonso checkpoint). vLLM chthonic/B12X, ModelOpt FP4, TP=4 no-Ray across 4 DGX Sparks, max_model_len=524288, gpu_memory_utilization=0.84, max_num_batched_tokens=8192, max_num_seqs=5."
```

Report paths from the run:

```text
results/runs/MiniMax-M3-NVFP4-vLLM-thinkOFF-64scen-v5c-4Spark-20260630-024756.md
results/runs/MiniMax-M3-NVFP4-vLLM-thinkOFF-64scen-v5c-4Spark-20260630-024756.html
results/artifacts/MiniMax-M3-NVFP4-vLLM-thinkOFF-64scen-v5c-4Spark-20260630-024756/
```

## Troubleshooting

If launch fails at `gpu_memory_utilization: 0.85` with a free-memory error, use `0.84`. The successful run used `0.84`.

If official NVIDIA checkpoint/runtime paths fail, use this `lukealonso/MiniMax-M3-NVFP4` + `ghcr.io/tonyd2wild/vllm-m3-chthonic:nccl230u1` path. The official checkpoint was tried first and hit DGX Spark runtime issues including unsupported B12X/FlashInfer/SM121 kernel combinations.

If throughput is unexpectedly low, verify the fabric interfaces and NCCL selection:

```bash
NCCL_DEBUG=VERSION
NCCL_SOCKET_IFNAME=enp1s0f0np0
GLOO_SOCKET_IFNAME=enp1s0f0np0
NCCL_IB_HCA=rocep1s0f0,roceP2p1s0f0
```

Also confirm the run is no-Ray PyTorch distributed and that all four nodes are on the 200G fabric.
