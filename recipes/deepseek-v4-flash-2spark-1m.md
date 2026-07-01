# DeepSeek V4 Flash 1M on 2x DGX Spark

This is the deployment pattern used for the 2026-07-01 Spark-Bench throughput/concurrency run.

Run id:

```text
DeepSeek-V4-Flash-throughput-2Spark-20260701-20260701-000411
```

## Short Answer

This was not our from-scratch recipe. It uses MiaAI-Lab's DeepSeek dual-DGX-Spark repo as the base, with credit to MiaAI-Lab for the original dual-Spark deployment work:

```text
https://github.com/MiaAI-Lab/DeepSeek-V4-Flash-Dual-DGX-Spark-1M-Context
/home/raulwesche/projects/DeepSeek-V4-Flash-Dual-DGX-Spark-1M-Context
```

The working benchmark was Mia's repo plus slight local runtime/config edits for our current Spark fabric. Both local and head-node clones have `origin` set to MiaAI-Lab, and both show local `docker-compose.yml` changes.

## What We Changed Locally

Compared with the checked-out MiaAI-Lab baseline, the active `docker-compose.yml` differs in these ways:

- `NCCL_IB_GID_INDEX` is read from env with a default: `${NCCL_IB_GID_INDEX:-3}`.
- `NCCL_CROSS_NIC` is pinned to `0` instead of `1` for one NIC/path.
- `NCCL_DEBUG=INFO` instead of `WARN` for bring-up/debug visibility.
- `--gpu-memory-utilization 0.83` instead of `0.82`.
- Added server generation defaults:
  `--override-generation-config '{"temperature":0.6,"top_p":0.95}'`.

The `.env` change that mattered for the July 1 run:

- Old/stale: `MASTER_ADDR=192.168.2.2`
- Working: `MASTER_ADDR=10.10.10.1`

That change was made on both the head and worker copies so the two-node vLLM rendezvous happened on the reachable fabric IP.

## Nodes Used

| Role | Host | Env | Value |
|---|---|---|---|
| head/rank 0 | spark-78f1 | `NODE_RANK` | `0` |
| head/rank 0 | spark-78f1 | `MASTER_ADDR` | `10.10.10.1` |
| head/rank 0 | spark-78f1 | `WORKER_HOST` | `10.0.0.229` |
| worker/rank 1 | spark-9f73 | `NODE_RANK` | `1` |
| worker/rank 1 | spark-9f73 | `HEADLESS` | `1` |
| worker/rank 1 | spark-9f73 | `MASTER_ADDR` | `10.10.10.1` |
| worker/rank 1 | spark-9f73 | `WORKER_HOST` | `10.0.0.229` |

Shared fabric settings:

```text
NCCL_IB_HCA=rocep1s0f0
NCCL_SOCKET_IFNAME=enp1s0f0np0
NCCL_IB_GID_INDEX=3
NCCL_IB_DISABLE=0
```

## Active Compose Settings

Image:

```text
aidendle94/sparkrun-vllm-ds4-gb10:production-ready
```

Important vLLM command settings:

```text
model: deepseek-ai/DeepSeek-V4-Flash
served model name: deepseek-v4-flash
tensor_parallel_size: 2
pipeline_parallel_size: 1
distributed_executor_backend: mp
nnodes: 2
master_port: 25000
kv_cache_dtype: fp8
block_size: 256
max_model_len: 1000000
max_num_seqs: 6
max_num_batched_tokens: 8192
gpu_memory_utilization: 0.83
speculative_config: {"method":"mtp","num_speculative_tokens":2}
tokenizer_mode: deepseek_v4
tool_call_parser: deepseek_v4
reasoning_parser: deepseek_v4
reasoning_config: {"reasoning_parser":"deepseek_v4","reasoning_start_str":"","reasoning_end_str":""}
default thinking: true
reasoning_effort: high
flashinfer_autotune: enabled
```

## Head `.env`

On `spark-78f1` / `10.10.10.1`:

```bash
NODE_RANK=0
HEADLESS=
MASTER_ADDR=10.10.10.1
WORKER_HOST=10.0.0.229
HF_CACHE=/home/raulwesche/.cache/huggingface
NCCL_IB_HCA=rocep1s0f0
NCCL_SOCKET_IFNAME=enp1s0f0np0
NCCL_IB_GID_INDEX=3
NCCL_IB_DISABLE=0
```

## Worker `.env`

On `spark-9f73` / `10.0.0.229`:

```bash
NODE_RANK=1
HEADLESS=1
MASTER_ADDR=10.10.10.1
WORKER_HOST=10.0.0.229
HF_CACHE=/home/raulwesche/.cache/huggingface
NCCL_IB_HCA=rocep1s0f0
NCCL_SOCKET_IFNAME=enp1s0f0np0
NCCL_IB_GID_INDEX=3
NCCL_IB_DISABLE=0
```

## Start

Launch from the head node only:

```bash
ssh 10.10.10.1
cd /home/raulwesche/projects/DeepSeek-V4-Flash-Dual-DGX-Spark-1M-Context
./start-deepseek-v4-flash.sh
```

The start script SSHs into `WORKER_HOST` first, starts the worker container, starts the head container, then polls:

```text
http://127.0.0.1:8000/v1/models
```

External benchmark endpoint used from the driver:

```text
http://10.10.10.1:8000/v1
```

Expected startup markers from the successful run:

```text
Loading target weights: about 186.69s
Loading drafter model: about 22.14s
Total model loading: about 231.39s
GPU KV cache size: about 2,871,094 tokens
Maximum concurrency for 1M request: about 2.87x
```

## Benchmark Command

```bash
cd /home/raulwesche/projects/spark-bench
PYTHONUNBUFFERED=1 python3 -u spark_bench.py tier2 \
  --label "DeepSeek-V4-Flash-throughput-2Spark-20260701" \
  --endpoint http://10.10.10.1:8000/v1 \
  --model deepseek-v4-flash \
  --contexts 1024,8192,32768 \
  --concurrency 1,2,4,8 \
  --conc-context 1024 \
  --gen-tokens 512 \
  --timeout 900 \
  --topology 2Spark-deepseek-10.10.10.1-10.0.0.229 \
  --parallelism TP2 \
  --spec-decode MTP2 \
  --notes "DeepSeek V4 Flash via MiaAI-Lab 2x DGX Spark repo, local fabric/env fixes, 1M context, fp8 KV, MTP2."
```

Future `spark_bench.py eval` runs append the same throughput side sweep automatically, so this standalone `tier2` command is only needed for throughput-only testing.

## Stop

Stop from the head node only:

```bash
ssh 10.10.10.1
cd /home/raulwesche/projects/DeepSeek-V4-Flash-Dual-DGX-Spark-1M-Context
./stop-deepseek-v4-flash.sh
```

Verify both sides are idle:

```bash
ssh 10.10.10.1 "docker ps --format '{{.Names}} {{.Status}} {{.Image}}'"
docker ps --format '{{.Names}} {{.Status}} {{.Image}}'
```

Both should return no DeepSeek containers.
