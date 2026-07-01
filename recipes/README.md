# Spark-Bench Deployment Recipes

Practical deployment notes for models benchmarked on NVIDIA DGX Spark.

Forward policy: for new vLLM-backed benchmark recipes, use the newest validated stable vLLM baseline available at setup time (v0.24.0 as of 2026-07-01), unless the model needs a pinned fork or container. Do not rerun existing leaderboard entries just for an engine upgrade; record the exact vLLM image, wheel, tag, or commit for each new run.

| Recipe | Hardware | Backend | Notes |
|--------|----------|---------|-------|
| [MiniMax-M3 NVFP4](minimax-m3-lukealonso-nvfp4.md) | 4x DGX Spark | vLLM chthonic/B12X | Exact 4-node TP=4 recipe used for the v5c 85.1 run |
| [MiMo V2.5 NVFP4 TP2 1M](mimo-v25-nvfp4-tp2-1m.md) | 2x DGX Spark | vLLM Ray TP2/MTP1 | Exact routed-NIC recipe used for the v5c 84.7 run and 2026-07-01 throughput sweep |
| [DeepSeek V4 Flash 1M](deepseek-v4-flash-2spark-1m.md) | 2x DGX Spark | vLLM mp TP2/MTP2 | MiaAI-Lab repo plus slight local fabric/env changes used for the 2026-07-01 throughput sweep |
| [Qwen3.6-27B NVIDIA NVFP4 + DFlash](qwen36-27b-nvidia-nvfp4-dflash.md) | 1x DGX Spark | vLLM nightly + DFlash | Tuned k=10 compile/CUDA graph recipe used for the v5c 81.0 run |
| [Step-3.7-Flash-NVFP4 MTP](step37-flash-nvfp4-mtp-2spark.md) | 2x DGX Spark | vLLM no-Ray TP2/MTP3 | MiaAI-Lab standalone recipe used for the v5c 66.8 run |
| [Ornith-1.0-35B MoE](ornith-35b-moe.md) | 1x DGX Spark | llama.cpp | Single-Spark GGUF deployment |
