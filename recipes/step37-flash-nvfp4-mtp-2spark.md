# Step-3.7-Flash-NVFP4 MTP on 2x DGX Spark

This is the exact 2-node Step-3.7-Flash-NVFP4 deployment used for the Spark-Bench v5c run:

```text
Step-3.7-Flash-NVFP4-MTP-vLLM-thinkOFF-64scen-v5c-2Spark-20260630-144114
```

Result: TrueScore **66.8**, median latency **10.97s**, eval throughput **48.1 tok/s**, **88,332** output tokens across 64 scenarios.

The deployment is based on the MiaAI-Lab advanced standalone MTP recipe:

```text
https://github.com/MiaAI-Lab/Dual-DGX-Spark-Step-3.7-Flash-NVFP4
```

This recipe uses vLLM no-Ray / PyTorch distributed tensor parallelism across two DGX Sparks. It is **MTP speculative decoding**, not Qwen-style DFlash.

## Cluster

| Role | SSH IP | Hostname | Fabric IP | NIC | RDMA HCAs |
|------|--------|----------|-----------|-----|-----------|
| rank 0 / head | `10.0.0.229` | `spark-9f73` | `10.10.10.3` | `enp1s0f0np0` | `rocep1s0f0,roceP2p1s0f0` |
| rank 1 / worker | `10.0.0.109` | `spark-78f1` | reachable from head | `enp1s0f0np0` | `rocep1s0f0,roceP2p1s0f0` |

The deployment config uses `HEAD_IP=10.10.10.3` and `WORKER_IP=10.0.0.109`. The worker is launched over management SSH, while vLLM/NCCL rendezvous uses the head fabric IP.

## Final config

```bash
MODEL=stepfun-ai/Step-3.7-Flash-NVFP4
SERVED_MODEL_NAME=Step-3.7-Flash-NVFP4-MTP
IMAGE=stepfun37-workspace:latest
BASE_IMAGE=vllm/vllm-openai:stepfun37
CONTAINER_NAME=vllm_node
PORT=8888

NNODES=2
TP_SIZE=2
MAX_MODEL_LEN=262144
MAX_NUM_BATCHED_TOKENS=8192
MAX_NUM_SEQS=8
GPU_MEMORY_UTILIZATION=0.85
MTP_NUM_SPECULATIVE_TOKENS=3

ETH_IF=enp1s0f0np0
IB_IF=rocep1s0f0,roceP2p1s0f0
MASTER_PORT=29501
NCCL_IB_GID_INDEX=3
```

Important launch flags inside the generated vLLM command:

```bash
vllm serve stepfun-ai/Step-3.7-Flash-NVFP4   --served-model-name Step-3.7-Flash-NVFP4-MTP   --host 0.0.0.0   --port 8888   --trust-remote-code   --tensor-parallel-size 2   --nnodes 2   --master-addr 10.10.10.3   --master-port 29501   --quantization modelopt   --kv-cache-dtype fp8   --max-model-len 262144   --max-num-batched-tokens 8192   --max-num-seqs 8   --gpu-memory-utilization 0.85   --disable-cascade-attn   --disable-custom-all-reduce   --no-enable-flashinfer-autotune   --enable-auto-tool-choice   --tool-call-parser step3p5   --reasoning-parser step3p5   --speculative-config '{"method":"mtp","num_speculative_tokens":3}'
```

Container env:

```bash
NCCL_SOCKET_IFNAME=enp1s0f0np0
GLOO_SOCKET_IFNAME=enp1s0f0np0
UCX_NET_DEVICES=enp1s0f0np0
NCCL_IB_HCA=rocep1s0f0,roceP2p1s0f0
NCCL_NET=IB
NCCL_CROSS_NIC=1
NCCL_IGNORE_CPU_AFFINITY=1
NCCL_IB_GID_INDEX=3
```

`NCCL_DEBUG=INFO` was useful while debugging but removed from the final shared recipe.

## Prerequisites

Clone the guide repo on the workstation and sync it to the head Spark:

```bash
git clone https://github.com/MiaAI-Lab/Dual-DGX-Spark-Step-3.7-Flash-NVFP4   /home/raulwesche/projects/Dual-DGX-Spark-Step-3.7-Flash-NVFP4
rsync -az --delete --exclude .git   /home/raulwesche/projects/Dual-DGX-Spark-Step-3.7-Flash-NVFP4/   10.0.0.229:/home/raulwesche/projects/Dual-DGX-Spark-Step-3.7-Flash-NVFP4/
```

Build/copy the wrapper image:

```bash
ssh 10.0.0.229 'cd /home/raulwesche/projects/Dual-DGX-Spark-Step-3.7-Flash-NVFP4 && ./build-image.sh && ./copy-image-to-worker.sh'
```

The model cache must be complete on both nodes:

```text
~/.cache/huggingface/hub/models--stepfun-ai--Step-3.7-Flash-NVFP4/
```

During setup, the worker cache was incomplete and had to be resynced from the head over fabric:

```bash
ssh 10.0.0.229 'rsync -a --delete --no-owner --no-group --omit-dir-times --exclude .no_exist --info=progress2   /home/raulwesche/.cache/huggingface/hub/models--stepfun-ai--Step-3.7-Flash-NVFP4/   10.10.10.1:/home/raulwesche/.cache/huggingface/hub/models--stepfun-ai--Step-3.7-Flash-NVFP4/'
```

Verify all safetensors before launch if a node was interrupted during download.

## Launch sequence

Start from empty containers on both selected Sparks:

```bash
ssh 10.0.0.229 'cd /home/raulwesche/projects/Dual-DGX-Spark-Step-3.7-Flash-NVFP4 && ./stop.sh'
```

Optional cold-start hygiene:

```bash
ssh 10.0.0.229 "sync; sudo -n sh -c 'echo 3 > /proc/sys/vm/drop_caches'"
ssh 10.0.0.109 "sync; sudo -n sh -c 'echo 3 > /proc/sys/vm/drop_caches'"
```

Launch MTP:

```bash
ssh 10.0.0.229 'cd /home/raulwesche/projects/Dual-DGX-Spark-Step-3.7-Flash-NVFP4 && ./start.sh mtp'
```

API:

```text
http://10.0.0.229:8888/v1
```

Served model:

```text
Step-3.7-Flash-NVFP4-MTP
```

## Successful startup markers

Expected markers from the final run:

```text
speculative_config={'method': 'mtp', 'num_speculative_tokens': 3}
Resolved architecture: Step3p7ForConditionalGeneration
Resolved architecture: Step3p5MTP
Detected ModelOpt NVFP4 checkpoint
Using FLASHINFER attention backend
Loading weights took about 178 seconds
Loading drafter model...
Loading weights took about 14.5 seconds
Detected MTP model. Sharing target model embedding weights with the draft model.
Model loading took 60.94 GiB memory and about 205 seconds
GPU KV cache size: 2,968,516 tokens
Maximum concurrency for 262,144 tokens per request: 11.32x
Application startup complete
```

Cold start is about 6-7 minutes after the model cache is already present and healthy.

## Verify

```bash
curl -sS http://10.0.0.229:8888/v1/models | python3 -m json.tool
```

Quick completion:

```bash
curl -sS http://10.0.0.229:8888/v1/chat/completions   -H 'Content-Type: application/json'   -d '{
    "model":"Step-3.7-Flash-NVFP4-MTP",
    "messages":[{"role":"user","content":"Say hi in one word."}],
    "max_tokens":16,
    "temperature":0,
    "chat_template_kwargs":{"thinking_mode":"disabled","enable_thinking":false}
  }' | python3 -m json.tool
```

## MTP tuning

MTP=3 was kept as the final recipe. A controlled fixed six-prompt probe was run after the benchmark:

| Setting | Probe throughput | Notes |
|---|---:|---|
| `num_speculative_tokens=3` | **27.56 tok/s** | Final recipe; faster despite lower third-token acceptance |
| `num_speculative_tokens=2` | 25.58 tok/s | Slightly higher nominal acceptance, lower useful throughput |

MTP=2 counters after the fixed probe:

```text
draft tokens: 3,016
accepted tokens: 2,000
acceptance: 66.3%
position 0: 1,224 / 1,508 = 81.2%
position 1: 776 / 1,508 = 51.5%
```

The MTP=3 cumulative counters after the benchmark plus probe showed about 65.5% draft-token acceptance, with the third position weaker:

```text
draft tokens: 122,724
accepted tokens: 80,365
position 0: 35,844 / 40,908 = 87.6%
position 1: 26,666 / 40,908 = 65.2%
position 2: 17,855 / 40,908 = 43.6%
```

Takeaway: do not tune only for acceptance percentage. MTP=3 delivered higher end-to-end throughput on the fixed probe and preserved full 262K context capacity.

## Spark-Bench v5c

```bash
cd /home/raulwesche/projects/spark-bench
python3 spark_bench.py eval   --label Step-3.7-Flash-NVFP4-MTP-vLLM-thinkOFF-64scen-v5c-2Spark   --endpoint http://10.0.0.229:8888/v1   --model Step-3.7-Flash-NVFP4-MTP   --parallelism 2   --spec-decode mtp3   --timeout 900   --repeats 2   --temperature 0.3   --thinking off   --tier all   --notes "Step-3.7-Flash-NVFP4 on 2x DGX Spark via MiaAI-Lab standalone no-Ray vLLM recipe, TP=2, MTP speculative decoding num_speculative_tokens=3, 262k context, NVFP4 target plus BF16 MTP graft."
```

Run outputs:

```text
results/runs/Step-3.7-Flash-NVFP4-MTP-vLLM-thinkOFF-64scen-v5c-2Spark-20260630-144114.md
results/runs/Step-3.7-Flash-NVFP4-MTP-vLLM-thinkOFF-64scen-v5c-2Spark-20260630-144114.html
results/artifacts/Step-3.7-Flash-NVFP4-MTP-vLLM-thinkOFF-64scen-v5c-2Spark-20260630-144114/
```

## Result notes

Strengths:

- Robustness: 100.0
- Long context: 100.0
- Visual: 85.2
- Agentic: 71.2
- Calibration: 97.2
- Reliability: 93.3

Weaknesses:

- Code domain scored 0.0 because benchmark extraction found no Python/SQL code in all 10 code cases.
- Classification scored 0.0 due JSON-array formatting failure.
- Strict instruction/structured formatting was inconsistent.

Post-benchmark game artifacts:

| Artifact | Finish | Notes |
|---|---|---|
| Frogger | `length` at 12,000 tokens | Extracted 4,743 HTML chars; truncated raw output, not repaired |
| Space Invaders | `length` at 8,000 tokens | API reported 8,000 completion tokens but content was empty; blank saved artifact, not repaired |
