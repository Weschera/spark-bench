# Deploying Ornith-1.0-35B MoE on DGX Spark

A practical deployment guide for running Ornith-1.0-35B MoE on a single NVIDIA DGX Spark (GB10 Grace-Blackwell, 128GB unified memory). Covers download, serving, tuning, and verification.

---

## Model Overview

| Property | Value |
|----------|-------|
| **Name** | Ornith-1.0-35B MoE |
| **Format** | Q4_K_M GGUF (19.7 GB) |
| **Total params** | 35B (Mixture-of-Experts) |
| **Active params** | 3B per token |
| **Context** | 65,536 tokens |
| **GPU memory** | ~20 GB weights + KV cache |

The MoE architecture means only 3B parameters are active per forward pass — that's why this model hits 66.9 tok/s on a single Spark despite being 35B total. For comparison, a dense 27B model on the same hardware does ~9 tok/s.

## Other Variants

| Variant | Available | Notes |
|---------|-----------|-------|
| 9B Dense | ✅ | Small, fast, lower quality |
| 31B Dense | ❌ | Announced but never published |
| 35B MoE | ✅ | **This guide** — best speed/quality balance |
| 397B MoE | ✅ | Needs 4× Sparks (FP8, multi-node) |

---

## 1. Download

### Install HuggingFace CLI (if needed)

```bash
pip install huggingface-hub
```

### Download the model

```bash
hf download <org>/Ornith-1.0-35B-MoE-GGUF \
  ornith-1.0-35b-Q4_K_M.gguf \
  --local-dir ~/models/ornith-35b
```

This downloads a single 19.7 GB file. Resumes automatically if interrupted.

### Verify

```bash
ls -lh ~/models/ornith-35b/
# Should show: ornith-1.0-35b-Q4_K_M.gguf  ~20G
```

---

## 2. Build llama.cpp with CUDA support

Ornith ships as GGUF — you need llama.cpp compiled for the GB10's sm_121a architecture.

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

mkdir build-cuda && cd build-cuda
cmake .. \
  -DGGML_CUDA=ON \
  -DCMAKE_CUDA_ARCHITECTURES=121a \
  -DGGML_CUDA_F16=ON
make -j$(nproc)
```

The server binary will be at `~/llama.cpp/build-cuda/bin/llama-server`.

> **Why not vLLM?** Ornith's GGUF format works natively with llama.cpp. vLLM requires safetensors. For this model, llama.cpp is the correct serving backend.

---

## 3. Serve the model

```bash
~/llama.cpp/build-cuda/bin/llama-server \
  -m ~/models/ornith-35b/ornith-1.0-35b-Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 8001 \
  -ngl 999 \
  -c 65536 \
  -fa on \
  -t 8 \
  -b 512
```

### Flag breakdown

| Flag | Value | Why |
|------|-------|-----|
| `-m` | model path | Path to the GGUF file |
| `--host 0.0.0.0` | all interfaces | Allow connections from other machines on the network |
| `--port 8001` | 8001 | Use 8001 to avoid conflicts with other services on 8000 |
| `-ngl 999` | all layers on GPU | Offload everything to the GB10 — 128GB unified memory handles it |
| `-c 65536` | 64K context | Enough for most workloads; higher uses more KV cache memory |
| `-fa on` | flash attention | Required for good throughput on GB10 — measurably faster |
| `-t 8` | 8 CPU threads | DGX Spark has 20 cores; 8 is a good balance for prompt processing |
| `-b 512` | batch size 512 | Controls prompt processing batch size — 512 is a safe default |

### Memory budget

| Component | Memory |
|-----------|-------:|
| Model weights (Q4_K_M) | ~20 GB |
| KV cache (64K context) | ~4-8 GB |
| CUDA runtime + overhead | ~2 GB |
| **Total** | **~26-30 GB** |

The DGX Spark has 128 GB unified memory, so this leaves plenty of room. You could run a second model alongside it if needed.

---

## 4. Verify the deployment

### Health check

```bash
curl -s http://localhost:8001/health
# {"status":"ok"}
```

### Quick inference test

```bash
curl -s http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ornith-1.0-35b-Q4_K_M.gguf",
    "messages": [{"role": "user", "content": "Write a Python function to check if a number is prime."}],
    "max_tokens": 200
  }' | python3 -m json.tool
```

### Check throughput

```bash
# Time a 256-token generation
time curl -s http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ornith-1.0-35b-Q4_K_M.gguf",
    "messages": [{"role": "user", "content": "Explain how MoE models work in 200 words."}],
    "max_tokens": 256,
    "stream": false
  }'
```

Expected: ~66 tok/s for single-stream generation.

---

## 5. Remote access (optional)

To serve other machines on your network:

```bash
# The server is already listening on 0.0.0.0:8001
# From another machine:
curl -s http://<spark-ip>:8001/v1/models
```

If using InfiniBand/RoCE between Sparks, the RoCE IP works too:

```bash
curl -s http://192.168.2.1:8001/v1/chat/completions ...
```

---

## 6. Performance tuning

### Higher throughput (multiple concurrent requests)

```bash
llama-server ... -c 131072 -b 1024 --parallel 4
```

- `-c 131072`: doubles context budget for concurrent sequences
- `--parallel 4`: allows 4 simultaneous requests

### Lower latency (single-stream)

```bash
llama-server ... -c 32768 -b 256 -t 4
```

- Smaller context = less KV cache = faster allocation
- Fewer threads reduces scheduling overhead for short prompts

### Quantization alternatives

| Quant | Size | Speed | Quality | Notes |
|-------|------|-------|---------|-------|
| Q4_K_M | 19.7 GB | 66.9 tok/s | 87.5 TrueScore | **Recommended** — best balance |
| Q5_K_M | ~23 GB | ~55 tok/s | marginally higher | If you have spare memory |
| Q3_K_L | ~16 GB | ~75 tok/s | lower | If running multiple models |
| Q8_0 | ~37 GB | ~40 tok/s | highest | Barely fits alongside KV cache |

---

## 7. Troubleshooting

### OOM / model won't load

```bash
# Check available memory
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# Reduce context size
llama-server ... -c 32768  # instead of 65536
```

### Slow token generation

- Ensure `-fa on` is set (flash attention)
- Ensure `-ngl 999` (all layers on GPU, not CPU fallback)
- Check `nvidia-smi` — GPU util should be near 100% during generation
- If other GPU processes are running, stop them (one model per GPU)

### Connection refused from other machines

- Verify `--host 0.0.0.0` (not `127.0.0.1`)
- Check firewall: `sudo ufw allow 8001/tcp`
- Verify network: `ping <spark-ip>` from the client machine

---

## Benchmark results

If you want to reproduce our benchmark numbers, here's how we tested it.

### spark-bench (57 scenarios, think-OFF)

```bash
git clone https://github.com/Weschera/spark-bench
cd spark-bench

python3 spark_bench.py eval \
  --label "Ornith-1.0-35B-thinkOFF-57scen" \
  --endpoint http://localhost:8001/v1 \
  --model "ornith-1.0-35b-Q4_K_M.gguf" \
  --thinking off --repeats 2 \
  --tier all --gen-tokens 256 --timeout 900
```

| Metric | Value |
|--------|------:|
| **TrueScore** | **87.5** |
| Tokens/sec | 66.9 |
| Median latency | 1.09s |
| Pass@1 | 91.2% |
| Pass@K | 82.5% |
| Quality | 75.3 |
| Calibration | 95.6 |
| Reliability | 94.9 |
| Efficiency | 100.0 |
| Responsiveness | 94.8 |

### tool-eval-bench

```bash
pip install tool-eval-bench

tool-eval-bench \
  --model ornith-1.0-35b-Q4_K_M.gguf \
  --backend llamacpp \
  --base-url http://localhost:8001/v1 \
  --no-think --trials 2 --timeout 120 \
  --json-file /tmp/ornith_toolbench.json \
  --output-dir /tmp/toolbench-ornith
```

| Metric | Value |
|--------|------:|
| Final Score | 84/100 |
| Deployability | 83 |
| Responsiveness | 80 |

### Key takeaways

- **3B active params** → 66.9 tok/s, 7.3× faster than dense 27B models on the same hardware
- **Structured output (JSON)**: perfect 100% — never produced invalid JSON
- **Visual generation**: 97.7 avg — correct orbital trigonometry, spiral particle systems, rotating DNA helix in pure HTML canvas
- **Weak spot**: multi-step tool chains — model struggled with sequential tool dependencies
