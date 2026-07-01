# Tier 2 — Inference (DeepSeek-V4-Flash-throughput-2Spark-20260701-20260701-000411)

- model `deepseek-v4-flash` @ `http://10.10.10.1:8000/v1`  topology `unknown` parallelism `2` spec_decode `mtp2`

## Single-stream decode

| context | TTFT (ms) | decode tok/s | TPOT (ms) | prefill tok/s | out toks |
|--------:|----------:|-------------:|----------:|--------------:|---------:|
| 1008 | 1123 | 38.4 | 26.1 | 898 | 512 |
| 7997 | 4021 | 38.5 | 26.0 | 1989 | 512 |
| 31951 | 13219 | 38.1 | 26.3 | 2417 | 512 |

## Throughput under concurrency

| batch | agg decode tok/s | per-stream tok/s | TTFT p50 (ms) | TTFT p99 (ms) | completed |
|------:|-----------------:|-----------------:|--------------:|--------------:|----------:|
| 1 | 38 | 39.5 | 508 | 508 | 1/1 |
| 2 | 55 | 33.0 | 2977 | 2978 | 2/2 |
| 4 | 72 | 19.3 | 687 | 688 | 4/4 |
| 8 | 98 | 23.6 | 1677 | 24589 | 8/8 |

