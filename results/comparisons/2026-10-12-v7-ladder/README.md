# v7.0 ladder: every valid full run so far (October 12, 2026)

All 33 rows ran the full **v7.0 suite**: 80 scenarios across 13 domains, 2 repeats (seeds 2001–2002), uncapped (each request may use the rest of the context window), sampling from each model's card. Every run is valid: golden gate passed and transport errors stay under the 5% limit (three hosted runs had one upstream timeout each, 1.2%). Per-run reports are in [`runs/`](runs/), with endpoints and host names scrubbed.

TrueScore = Quality 55% · Calibration (safety + robustness) 25% · Reliability (repeat consistency) 15% · speed 5%.

## Thinking ON

| # | Model | Quant | Engine / recipe | Hardware | TrueScore | Quality | Calibration | Reliability |
|---:|---|---|---|---|---:|---:|---:|---:|
| 1 | [missingno (stealth, unnamed) ¹ ²](runs/missingno-nous-free.md) | unknown | Nous Portal free API | hosted | **91.2** | 88.0 | 100.0 | 94.8 |
| 2 | [GLM-5.3-Flash](runs/glm53-flash-4bpw-tf-tp2-on.md) | EXL3 4bpw | TensorFold v0.6.0 + DFlash2 (Mia recipe v1.8) | 2 Sparks TP2 | **88.9** | 91.3 | 88.5 | 93.2 |
| 3 | [DeepSeek-V4.1-Flash ²](runs/deepseek-v4.1-flash-exl3-2.9-tp2-on.md) | EXL3 2.9bpw | vLLM + EXL3, DSpark k5 (Mia recipe) | 2 Sparks TP2 | **88.7** | 90.2 | 90.9 | 95.1 |
| 4 | [RED-SNOW-5.3-Flash](runs/red-snow-4.91-tf-tp2-on.md) | EXL3 SAGE 4.91bpw | TensorFold TP2 + DFlash2 (Justin Casey recipe) + unclosed-think fix | 2 Sparks TP2 | **87.7** | 90.1 | 85.9 | 90.2 |
| 5 | [Step 5 preview ¹](runs/step5-preview-nous-free.md) | unknown | Nous Portal free API | hosted | **84.2** | 82.3 | 94.3 | 82.6 |

## Thinking OFF

| # | Model | Quant | Engine / recipe | Hardware | TrueScore | Quality | Calibration | Reliability |
|---:|---|---|---|---|---:|---:|---:|---:|
| 1 | [Nemotron-3-Ultra 550B-A55B](runs/nemotron-3-ultra-nvfp4-sglang-tp4-off.md) | NVFP4 | SGLang 0.5.12 TP4+EP4 | 4 Sparks TP4 | **90.0** | 86.4 | 100.0 | 94.3 |
| 2 | [DeepSeek-V4.1-Flash](runs/deepseek-v4.1-flash-exl3-2.9-tp2-off.md) | EXL3 2.9bpw | vLLM + EXL3, DSpark k5 (Mia recipe) | 2 Sparks TP2 | **89.5** | 89.0 | 90.5 | 91.4 |
| 3 | [RED-SNOW-5.3-Flash](runs/red-snow-4.91-tf-tp2-off.md) | EXL3 SAGE 4.91bpw | TensorFold TP2 + DFlash2 (Justin Casey recipe) | 2 Sparks TP2 | **87.0** | 86.2 | 87.0 | 90.8 |
| 4 | [Qwen3.8-27B](runs/qwen38-27b-bf16-mlxlm-mac-off.md) | BF16 | mlx-lm 0.32.0 | Mac Studio M4 Max | **86.7** | 83.7 | 97.3 | 89.8 |
| 5 | [RED-SNOW-5.3-Flash ³](runs/red-snow-2.49-exl3-1spark-off.md) | EXL3 SAGE 2.49bpw | exllamav3 + MTP2 (@vic305) | 1 Spark | **85.1** | 83.6 | 85.3 | 92.0 |
| 6 | [GLM-5.3-Flash ³](runs/glm53-flash-4bpw-tf-tp2-off.md) | EXL3 4bpw | TensorFold v0.6.0 + DFlash2 (Mia recipe v1.8) | 2 Sparks TP2 | **84.8** | 82.6 | 86.7 | 88.4 |
| 7 | [Qwen3.8-27B](runs/qwen38-27b-mlx8-tf-dflash2-mac-off.md) | MLX 8-bit | TensorFold 0.6.5 MLX + DFlash2 | Mac Studio M4 Max | **84.7** | 81.1 | 89.5 | 91.0 |
| 8 | [Laguna XS 2.1](runs/laguna-xs-2.1-nous-free.md) | unknown | Nous Portal free API | hosted | **84.6** | 78.7 | 93.4 | 89.9 |
| 9 | [Ling 3.1 Flash](runs/ling-3.1-flash-nous-free.md) | unknown | Nous Portal free API | hosted | **84.5** | 79.5 | 91.4 | 90.9 |
| 10 | [GLM-5.3 (full)](runs/glm53-full-exl3-3.38-tf-tp4-off.md) | EXL3 SAGE 3.38bpw | TensorFold TP4 + DFlash2 (@vic305 recipe) | 4 Sparks TP4 | **84.4** | 82.5 | 88.0 | 90.0 |
| 11 | [LongCat 2.5 preview](runs/longcat-2.5-preview-nous-free.md) | unknown | Nous Portal free API | hosted | **84.3** | 78.9 | 92.8 | 91.5 |
| 12 | [Qwen3.8-27B](runs/qwen38-27b-bf16-vllm-1spark-off.md) | BF16 | vLLM 0.31.0, MTP k3 | 1 Spark | **84.3** | 82.3 | 88.8 | 91.2 |
| 13 | [Laguna S 2.1](runs/laguna-s-2.1-nous-free.md) | unknown | Nous Portal free API | hosted | **84.0** | 76.5 | 98.0 | 88.3 |
| 14 | [Qwen3.8-27B](runs/qwen38-27b-mlx4-tf-dflash2-mac-off.md) | MLX 4-bit | TensorFold 0.6.5 MLX + DFlash2 | Mac Studio M4 Max | **83.6** | 83.0 | 82.2 | 87.5 |
| 15 | [Qwen3.8-27B ³](runs/qwen38-27b-mlx4-tf-1spark-off.md) | MLX 4-bit | TensorFold 0.6.5 + DFlash2 | 1 Spark | **82.9** | 81.1 | 81.7 | 89.1 |
| 16 | [MiMo-V2.6-Flash-RL](runs/mimo-v2.6-flash-mxfp4-vllm-tp2-off.md) | MXFP4 | vLLM, DFlash k7, rep penalty 1.05 (Tony recipe default) | 2 Sparks TP2 | **82.5** | 82.6 | 80.1 | 85.1 |
| 17 | [Nemotron-3-Super 120B-A12B](runs/nemotron-3-super-nvfp4-vllm-1spark-off.md) | NVFP4 | vLLM 0.31.0, MTP k3 | 1 Spark | **82.3** | 76.6 | 91.4 | 88.1 |
| 18 | [Qwen3.8-27B](runs/qwen38-27b-mlx4-mlxlm-mac-off.md) | MLX 4-bit | mlx-lm 0.32.0 | Mac Studio M4 Max | **81.4** | 80.2 | 80.7 | 90.1 |
| 19 | [Solar Mini 4 ²](runs/solar-mini-4-nous-free.md) | unknown | Nous Portal free API | hosted | **81.2** | 74.4 | 88.4 | 91.4 |
| 20 | [Qwen3.8-Flash-Next ³](runs/qwen38-flash-next-nvfp4-vllm-tp2-off.md) | NVFP4 (RadixArk) | vLLM TP2+EP+MTP3 (Mia recipe) | 2 Sparks TP2 | **79.4** | 77.3 | 78.2 | 86.1 |
| 21 | [Qwen3.8-Flash-Next ³](runs/qwen38-flash-next-mlx4-tf-1spark-off.md) | MLX 4-bit | TensorFold 0.6.5 + MTP | 1 Spark | **78.5** | 72.5 | 84.0 | 86.6 |
| 22 | [Qwen3.8-Flash-Next ³](runs/qwen38-flash-next-nvfp4-tf-tp2-off.md) | NVFP4 (nvidia) | TensorFold Zig (Mia recipe) | 2 Sparks TP2 | **77.9** | 78.3 | 69.9 | 85.3 |
| 23 | [Nemotron-3.5-Lightning 30B-A3B ²](runs/nemotron-3.5-lightning-nvfp4-vllm-1spark-off.md) | NVFP4 | vLLM 0.31.0, DSpark k3 | 1 Spark | **76.8** | 67.2 | 86.9 | 89.2 |
| 24 | [CYBER-FROST-3.8 ³](runs/cyber-frost-3.8-exl3-3.87-1spark-off.md) | EXL3 SAGE 3.87bpw | exllamav3 + TabbyAPI (@vic305) | 1 Spark | **74.7** | 75.2 | 65.7 | 86.3 |
| 25 | [Ling-3.0-flash ²](runs/ling-3.0-flash-int4-sglang-1spark-off.md) | INT4 | SGLang, DSpark draft | 1 Spark | **74.7** | 64.1 | 89.5 | 83.2 |
| 26 | [Nemotron-3-Nano-Omni 30B-A3B ²](runs/nemotron-3-nano-omni-nvfp4-vllm-1spark-off.md) | NVFP4 | vLLM 0.31.0 | 1 Spark | **74.0** | 64.4 | 82.6 | 89.4 |
| 27 | [Nemotron-3-Nano 30B-A3B ²](runs/nemotron-3-nano-nvfp4-vllm-1spark-off.md) | NVFP4 | vLLM 0.31.0 | 1 Spark | **73.9** | 59.1 | 94.6 | 87.9 |
| 28 | [Nemotron-3.5-Lightning 30B-A3B](runs/nemotron-3.5-lightning-mlx4-tf-1spark-off.md) | MLX 4-bit | TensorFold 1.0.2 native CUDA, MTP | 1 Spark | **71.0** | 64.1 | 73.4 | 83.9 |

¹ **Thinking always on.** The run requested thinking off (`--thinking off`, `reasoning.enabled=false`), but the hosted model reasons anyway, so it is ranked with the thinking-ON rows. Its report header says "thinking OFF" because that is what was requested.
² **FLAT_DOMAIN flag.** The harness flags a domain where every scenario scored exactly 0 or exactly 1. It means "verify", not "invalid", and the flag is left visible in the report:
- missingno (stealth, unnamed) (unknown, hosted): `FLAT_DOMAIN:code=1`
- DeepSeek-V4.1-Flash (EXL3 2.9bpw, 2 Sparks TP2): `FLAT_DOMAIN:code=1;FLAT_DOMAIN:instruction=1;FLAT_DOMAIN:planning=1`
- Solar Mini 4 (unknown, hosted): `FLAT_DOMAIN:planning=1`
- Nemotron-3.5-Lightning 30B-A3B (NVFP4, 1 Spark): `FLAT_DOMAIN:long_gen=0`
- Ling-3.0-flash (INT4, 1 Spark): `FLAT_DOMAIN:long_gen=0`
- Nemotron-3-Nano-Omni 30B-A3B (NVFP4, 1 Spark): `FLAT_DOMAIN:long_gen=0`
- Nemotron-3-Nano 30B-A3B (NVFP4, 1 Spark): `FLAT_DOMAIN:long_gen=0`

³ Ran on the pre-release branch at grader `15c65bc`, so the report says `v6.8.3-full-uncapped`. Same 80 scenarios and graders as v7.0; the release only renamed the labels.

## Reading these numbers

- **Rows are deployments, not models.** Engine, quant, hardware, drafter and sampling differ between rows. Gaps under about 1 point are run-to-run noise.
- **Hosted rows (Nous Portal free API) are ranked on quality only.** Their speed and latency include internet delay and shared servers, so their efficiency/responsiveness components are not comparable with local rows. "missingno" is an unnamed test model; what it is and whether it changes are unknown.
- **RED-SNOW thinking ON needed a server fix.** With thinking on, RED-SNOW often answers without closing its `<think>` block, so the server returned the answer as reasoning and the grader saw an empty reply. The 4.91 row ran with a patch that returns such a reply as content when it ended normally with no answer and no tool calls. The earlier run without the fix is excluded.
- **MiMo-V2.6** uses the recipe author's default repetition penalty 1.05; all other rows use none.
- **About 12 of the 80 scenarios are perfect for every model above 82**, so the top of the ladder is compressed. Dropping them lowers every score by 1–3 points and swaps only neighbours that were within 0.2.

## Excluded

- **RED-SNOW 4.91 thinking ON, first run:** stopped at 72/80; answers landed in reasoning (see the fix above).
- **RED-SNOW 2.49 thinking ON, first run:** stopped at 14/80 for the same reason; the fixed rerun is still in progress.
- **Step 3.7 Flash (Nous free):** aborted by the tool-call preflight; it never returned structured tool calls.
- Two listed free models were unavailable at run time.

## Still running

RED-SNOW 2.49 thinking ON (1 Spark, fixed server), Qwen3.8-27B MLX-8bit thinking ON (Mac Studio), GLM-5.3 full 3.38bpw thinking ON (4 Sparks, queued).

## Credits

Quants and recipes: @vic305 (RED-SNOW and CYBER-FROST EXL3, exllamav3 1-Spark path, GLM-5.3 full recipe), Justin Casey (RED-SNOW 2-Spark TensorFold recipe), MiaAI-Lab (GLM-5.3-Flash, DeepSeek-V4.1 and Qwen3.8-Flash-Next recipes), Tony (MiMo recipe), RadixArk and NVIDIA (NVFP4 checkpoints). Engines: TensorFold (@ashxhart), exllamav3 (turboderp), vLLM, SGLang, mlx-lm.
