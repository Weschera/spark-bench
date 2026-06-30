# Spark-Bench Deployment Recipes

Practical deployment notes for models benchmarked on NVIDIA DGX Spark.

| Recipe | Hardware | Backend | Notes |
|--------|----------|---------|-------|
| [MiniMax-M3 NVFP4](minimax-m3-lukealonso-nvfp4.md) | 4x DGX Spark | vLLM chthonic/B12X | Exact 4-node TP=4 recipe used for the v5c 85.1 run |
| [Qwen3.6-27B NVIDIA NVFP4 + DFlash](qwen36-27b-nvidia-nvfp4-dflash.md) | 1x DGX Spark | vLLM nightly + DFlash | Tuned k=10 compile/CUDA graph recipe used for the v5c 81.0 run |
| [Ornith-1.0-35B MoE](ornith-35b-moe.md) | 1x DGX Spark | llama.cpp | Single-Spark GGUF deployment |
