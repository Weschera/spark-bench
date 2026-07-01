# Tier 2 — Inference (Step-3.7-Flash-NVFP4-MTP-throughput-2Spark-20260701-20260630-234946)

- model `Step-3.7-Flash-NVFP4-MTP` @ `http://10.0.0.229:8888/v1`  topology `unknown` parallelism `2` spec_decode `mtp3`

## Single-stream decode

| context | TTFT (ms) | decode tok/s | TPOT (ms) | prefill tok/s | out toks |
|--------:|----------:|-------------:|----------:|--------------:|---------:|
| 1016 | 1291 | 25.9 | 38.6 | 787 | 512 |
| 8005 | 3602 | 30.2 | 33.1 | 2223 | 512 |
| 31959 | 11555 | 29.6 | 33.9 | 2766 | 512 |

## Throughput under concurrency

| batch | agg decode tok/s | per-stream tok/s | TTFT p50 (ms) | TTFT p99 (ms) | completed |
|------:|-----------------:|-----------------:|--------------:|--------------:|----------:|
| 1 | 28 | 28.5 | 281 | 281 | 1/1 |
| 2 | 53 | 27.4 | 554 | 554 | 2/2 |
| 4 | 72 | 18.9 | 248 | 249 | 4/4 |
| 8 | 155 | 20.1 | 292 | 294 | 8/8 |

