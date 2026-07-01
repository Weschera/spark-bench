# Tier 2 — Inference (MiMo-V2.5-NVFP4-throughput-2Spark-20260701-20260701-003210)

- model `MiMo-V2.5-NVFP4` @ `http://127.0.0.1:8000/v1`  topology `unknown` parallelism `2` spec_decode `mtp1`

## Single-stream decode

| context | TTFT (ms) | decode tok/s | TPOT (ms) | prefill tok/s | out toks |
|--------:|----------:|-------------:|----------:|--------------:|---------:|
| 1033 | 3780 | 28.8 | 34.7 | 273 | 505 |
| 8022 | 4731 | 23.5 | 42.7 | 1696 | 512 |
| 31976 | 32819 | 15.3 | 65.6 | 974 | 464 |

## Throughput under concurrency

| batch | agg decode tok/s | per-stream tok/s | TTFT p50 (ms) | TTFT p99 (ms) | completed |
|------:|-----------------:|-----------------:|--------------:|--------------:|----------:|
| 1 | 27 | 28.5 | 444 | 444 | 1/1 |
| 2 | 41 | 23.6 | 1235 | 1235 | 2/2 |
| 4 | 63 | 17.8 | 764 | 764 | 4/4 |
| 8 | 97 | 13.7 | 935 | 937 | 8/8 |

