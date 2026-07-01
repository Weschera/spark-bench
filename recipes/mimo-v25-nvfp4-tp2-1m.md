# MiMo V2.5 NVFP4 TP2 1M on 2x DGX Spark

This is the exact deployment pattern used for the Spark-Bench v5c MiMo run and the 2026-07-01 throughput/concurrency benchmark.

Result run ids:

```text
MiMo-V2.5-NVFP4-vLLM-TP2-1M-NVFP4KV-MTP1-thinkOFF-64scen-v5c-2Spark-20260630-072647
MiMo-V2.5-NVFP4-throughput-2Spark-20260701-20260701-003210
```

## Short Answer

The benchmark used the Tony/2Wild TP2 recipe as the base, from:

```text
/home/raulwesche/projects/MiMo-V2.5-TP2-1M-NVFP4-KV-2xDGX-Spark
https://github.com/tonyd2wild/MiMo-V2.5-TP2-1M-NVFP4-KV-2xDGX-Spark
```

No local source changes were left in that recipe clone. `git status --short` was clean after the run.

What was changed for our benchmark was runtime configuration, not recipe files:

- Used the shipped `recipe/run-container.sh`, `recipe/apply-mods.sh`, `recipe/run-head.sh`, `recipe/run-worker.sh`, and `recipe/launch.sh`.
- Applied the recipe's vendored mods inside both containers.
- Overrode the fabric IP/interface/HCA because the default documented `10.10.10.3`/`10.10.10.1` pair hung at NCCL init on the current routing state.
- Overrode the serving scheduler settings to the latest C8-friendly checkpoint: `MAX_NUM_SEQS=8`, `MAX_NUM_BATCHED_TOKENS=2048`, `BLOCK_SIZE=64`.

## Nodes Used

| Role | Host | SSH/control IP | Ray/vLLM RoCE IP used | Interface | HCA |
|---|---|---:|---:|---|---|
| head/rank 0 | spark-9f73 | `10.0.0.229` | `10.10.10.4` | `enP2p1s0f0np0` | `roceP2p1s0f0` |
| worker/rank 1 | spark-78f1 | `10.10.10.1` during this session | `10.10.10.2` | `enP2p1s0f0np0` | `roceP2p1s0f0` |

The initial launch tried the documented pair:

```text
HEAD_ROCE_IP=10.10.10.3
WORKER_ROCE_IP=10.10.10.1
NCCL_SOCKET_IFNAME=enp1s0f0np0
NCCL_IB_HCA=rocep1s0f0
```

That hung at NCCL init. `ip route get` showed this host was actually routing the peer over the other NIC:

```text
local -> peer: dev enP2p1s0f0np0 src 10.10.10.4
remote -> local: dev enP2p1s0f0np0 src 10.10.10.2
```

So the working launch pinned Ray, Gloo, NCCL, and vLLM to the routed pair.

## Start Containers and Apply Mods

Run on both nodes from the recipe directory:

```bash
cd /home/raulwesche/projects/MiMo-V2.5-TP2-1M-NVFP4-KV-2xDGX-Spark/recipe
CONTAINER=vllm_mimo_tp2 bash run-container.sh
bash apply-mods.sh vllm_mimo_tp2
```

The container image is the recipe default:

```text
ghcr.io/tonyd2wild/mimo-v2.5-tp2-1m-nvfp4kv:20260620
```

The mods applied by `apply-mods.sh` are:

```text
drop-caches
ray-keep-node-nccl-hca
fix-prometheus-instrumentator-router
fix-mimo-v2-vllm
fix-modelopt-mixed-mxfp8
nvfp4-kv-diffkv
```

Those mods patch the vLLM container at runtime. No extra hand patch was applied outside the recipe mods.

## Shared Runtime Exports

Use these inside the container on both nodes before `run-head.sh`, `run-worker.sh`, or `launch.sh`:

```bash
cd /workspace/recipe
source env.sh

export MODEL_PATH=/root/.cache/huggingface/hub/models--lukealonso--MiMo-V2.5-NVFP4/snapshots/a147dd04d6cf861e43b2d783dcde23b53ab7ee68
export SERVED_MODEL_NAME=MiMo-V2.5-NVFP4

export HEAD_ROCE_IP=10.10.10.4
export WORKER_ROCE_IP=10.10.10.2
export NCCL_SOCKET_IFNAME=enP2p1s0f0np0
export GLOO_SOCKET_IFNAME=enP2p1s0f0np0
export NCCL_IB_HCA=roceP2p1s0f0

export MAX_MODEL_LEN=1000000
export GPU_MEMORY_UTILIZATION=0.84
export MAX_NUM_SEQS=8
export MAX_NUM_BATCHED_TOKENS=2048
export BLOCK_SIZE=64
export MTP_SPEC_TOKENS=1
export VLLM_MIMO_MTP1_GREEDY_FAST=1
```

Notes:

- `env.sh` defaults still provide the important NVFP4/Ray stability settings: `LOAD_FORMAT=safetensors`, `VLLM_ALLOW_LONG_MAX_MODEL_LEN=1`, NVFP4 FlashInfer/CUTLASS env, Ray memory monitor disable, and `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.
- `MAX_NUM_SEQS=8`, `MAX_NUM_BATCHED_TOKENS=2048`, and `BLOCK_SIZE=64` match the latest concurrency checkpoint used for the benchmark.

## Start Ray

On the head container:

```bash
cd /workspace/recipe
source env.sh
export HEAD_ROCE_IP=10.10.10.4
export WORKER_ROCE_IP=10.10.10.2
export NCCL_SOCKET_IFNAME=enP2p1s0f0np0
export GLOO_SOCKET_IFNAME=enP2p1s0f0np0
export NCCL_IB_HCA=roceP2p1s0f0
bash run-head.sh
```

On the worker container:

```bash
cd /workspace/recipe
source env.sh
export HEAD_ROCE_IP=10.10.10.4
export WORKER_ROCE_IP=10.10.10.2
export NCCL_SOCKET_IFNAME=enP2p1s0f0np0
export GLOO_SOCKET_IFNAME=enP2p1s0f0np0
export NCCL_IB_HCA=roceP2p1s0f0
bash run-worker.sh
```

On the head, wait until Ray sees both GPUs:

```bash
until ray status 2>/dev/null | grep -qE '2\.0/2\.0 GPU|2\.0 GPU'; do sleep 2; done
```

## Launch vLLM

Run on the head container:

```bash
cd /workspace/recipe
source env.sh

export MODEL_PATH=/root/.cache/huggingface/hub/models--lukealonso--MiMo-V2.5-NVFP4/snapshots/a147dd04d6cf861e43b2d783dcde23b53ab7ee68
export SERVED_MODEL_NAME=MiMo-V2.5-NVFP4
export HEAD_ROCE_IP=10.10.10.4
export WORKER_ROCE_IP=10.10.10.2
export VLLM_HOST_IP=10.10.10.4
export NCCL_SOCKET_IFNAME=enP2p1s0f0np0
export GLOO_SOCKET_IFNAME=enP2p1s0f0np0
export NCCL_IB_HCA=roceP2p1s0f0
export MAX_MODEL_LEN=1000000
export GPU_MEMORY_UTILIZATION=0.84
export MAX_NUM_SEQS=8
export MAX_NUM_BATCHED_TOKENS=2048
export BLOCK_SIZE=64
export MTP_SPEC_TOKENS=1
export VLLM_MIMO_MTP1_GREEDY_FAST=1

bash launch.sh
```

Expected endpoint:

```text
http://10.0.0.229:8000/v1
# or from the head itself: http://127.0.0.1:8000/v1
```

Expected startup markers from the successful benchmark run:

```text
GPU KV cache size: about 2.17M tokens
Maximum concurrency for 1,000,000 tokens per request: about 2.17x
Model loading memory: about 86.2 GiB
```

## Smoke Test

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model":"MiMo-V2.5-NVFP4",
    "messages":[{"role":"user","content":"Reply exactly: OK 1M MTP1"}],
    "max_tokens":16,
    "temperature":0,
    "repetition_penalty":1.08,
    "chat_template_kwargs":{"enable_thinking":false}
  }'
```

Expected content includes:

```text
OK 1M MTP1
```

## Benchmark Commands

Original v5c eval run:

```bash
cd /home/raulwesche/projects/spark-bench
PYTHONUNBUFFERED=1 python3 -u spark_bench.py eval \
  --label "MiMo-V2.5-NVFP4-vLLM-TP2-1M-NVFP4KV-MTP1-thinkOFF-64scen-v5c-2Spark" \
  --endpoint http://10.0.0.229:8000/v1 \
  --model MiMo-V2.5-NVFP4 \
  --thinking off \
  --repeats 2 \
  --tier all \
  --gen-tokens 256 \
  --timeout 600 \
  --notes "MiMo V2.5 NVFP4. vLLM TP2 across 2 DGX Sparks, 1M max_model_len, NVFP4 KV, MTP1."
```

Throughput/concurrency run:

```bash
cd /home/raulwesche/projects/spark-bench
PYTHONUNBUFFERED=1 python3 -u spark_bench.py tier2 \
  --label "MiMo-V2.5-NVFP4-throughput-2Spark-20260701" \
  --endpoint http://127.0.0.1:8000/v1 \
  --model MiMo-V2.5-NVFP4 \
  --contexts 1024,8192,32768 \
  --concurrency 1,2,4,8 \
  --conc-context 1024 \
  --gen-tokens 512 \
  --timeout 900 \
  --topology 2Spark-routed-10.10.10.4-10.10.10.2 \
  --parallelism TP2 \
  --spec-decode MTP1 \
  --notes "MiMo V2.5 NVFP4 TP2 1M, NVFP4 KV, MTP1, routed f0 RoCE pair."
```

Future v5c eval runs now append this throughput sweep automatically from `spark_bench.py eval`, so the separate `tier2` command is only needed for standalone throughput-only testing.

## Stop and Cleanup

From the head host/container session, stop vLLM with Ctrl-C if it is foregrounded, then remove the containers on both nodes:

```bash
docker rm -f vllm_mimo_tp2
ssh 10.10.10.1 'docker rm -f vllm_mimo_tp2'
```

Verify idle state:

```bash
docker ps --format '{{.Names}} {{.Status}} {{.Image}}'
ssh 10.10.10.1 "docker ps --format '{{.Names}} {{.Status}} {{.Image}}'"
```

Both should return no MiMo containers.
