#!/usr/bin/env python3
"""
MOA Benchmark Proxy — exposes Hermes's REAL Mixture-of-Agents pipeline
as an OpenAI-compatible /v1/chat/completions endpoint for spark_bench.

This imports and uses the actual Hermes MOA code:
  - agent.moa_loop.MoAChatCompletions (the same facade the gateway uses)
  - agent.moa_loop._reference_messages, _REFERENCE_SYSTEM_PROMPT, _run_references_parallel
  - agent.auxiliary_client.call_llm (the same LLM caller the agent uses)
  - hermes_cli.moa_config.resolve_moa_preset (reads the real config)
  - hermes_cli.runtime_provider.resolve_runtime_provider (real provider resolution)

The ONLY thing this proxy does is bridge HTTP → MoAChatCompletions.create().
No reimplementation of prompts, message formatting, or model calls.

Usage:
  python3 moa_bench_proxy.py --port 8890

  # Then run spark_bench against it:
  cd ~/projects/spark-bench
  ./spark_bench.py eval \
    --label moa-3local-v5c \
    --endpoint http://localhost:8890/v1 \
    --model moa-local \
    --thinking off --repeats 2 \
    --tier all --gen-tokens 256 --timeout 1200
"""

import argparse
import json
import os
import sys
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler, ThreadingHTTPServer
from socketserver import ThreadingMixIn

# ── Bootstrap Hermes environment ─────────────────────────────────────
# Must set HERMES_HOME + HERMES_PROFILE before importing hermes modules
# so the MOA config resolver loads the x-poster profile's config.yaml
HERMES_HOME = os.path.expanduser("~/.hermes/profiles/x-poster")
os.environ["HERMES_HOME"] = HERMES_HOME
os.environ.setdefault("HERMES_PROFILE", "x-poster")

# Add Hermes source to path
HERMES_SRC = os.path.expanduser("~/.hermes/hermes-agent")
if HERMES_SRC not in sys.path:
    sys.path.insert(0, HERMES_SRC)


def _load_moa_facade():
    """Import and instantiate the real Hermes MoAChatCompletions facade."""
    from hermes_cli.config import load_config
    from hermes_cli.moa_config import resolve_moa_preset, normalize_moa_config
    from agent.moa_loop import MoAChatCompletions

    config = load_config()
    moa_cfg = config.get("moa") or {}
    normalized = normalize_moa_config(moa_cfg)
    default_preset = normalized.get("default_preset", "default")

    print(f"[moa-bench] Config loaded from {HERMES_HOME}/config.yaml")
    print(f"[moa-bench] Default preset: {default_preset}")

    preset = resolve_moa_preset(moa_cfg, default_preset)
    refs = preset.get("reference_models", [])
    agg = preset.get("aggregator", {})
    ref_labels = [f"{r['provider']}:{r['model']}" for r in refs]
    print(f"[moa-bench] Reference models: {', '.join(ref_labels)}")
    print(f"[moa-bench] Aggregator: {agg.get('provider')}:{agg.get('model')}")
    print(f"[moa-bench] Reference temp: {preset.get('reference_temperature', 0.6)}")
    print(f"[moa-bench] Aggregator temp: {preset.get('aggregator_temperature', 0.4)}")

    facade = MoAChatCompletions(preset_name=default_preset)
    return facade


# Global facade instance — initialized once at startup
_FACADE = None


class MOAHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[moa-bench] {args[0] if args else ''}")

    def do_GET(self):
        if self.path == "/v1/models":
            models = {
                "object": "list",
                "data": [{
                    "id": "moa-local",
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "hermes-moa",
                }],
            }
            self._json_response(200, models)
        elif self.path == "/health":
            self._json_response(200, {"status": "ok", "facade_ready": _FACADE is not None})
        else:
            self._json_response(404, {"error": "not found"})

    def do_POST(self):
        if not self.path.startswith("/v1/chat/completions"):
            self._json_response(404, {"error": "not found"})
            return

        content_len = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_len).decode("utf-8"))

        messages = body.get("messages", [])
        stream = body.get("stream", False)
        temperature = body.get("temperature", 0.4)
        max_tokens = body.get("max_tokens")
        tools = body.get("tools")
        extra = {}
        if "chat_template_kwargs" in body:
            extra["chat_template_kwargs"] = body["chat_template_kwargs"]

        t0 = time.perf_counter()
        ts = time.strftime("%H:%M:%S")
        print(f"[moa-bench {ts}] request: {len(messages)} messages, stream={stream}, tools={len(tools) if tools else 0}", flush=True)

        if stream:
            self._handle_stream(messages, temperature, max_tokens, tools, extra, t0)
        else:
            self._handle_nonstream(messages, temperature, max_tokens, tools, extra, t0)

    def _handle_nonstream(self, messages, temperature, max_tokens, tools, extra, t0):
        """Non-streaming: call the real MoA facade and return a complete response."""
        try:
            # MoAChatCompletions.create() accepts the same kwargs as OpenAI client.create()
            api_kwargs = {
                "messages": messages,
                "temperature": temperature,
            }
            if max_tokens is not None:
                api_kwargs["max_tokens"] = max_tokens
            if tools:
                api_kwargs["tools"] = tools
                api_kwargs["tool_choice"] = "auto"
            api_kwargs.update(extra)

            # The facade returns an OpenAI-compatible response object
            response = _FACADE.create(**api_kwargs)

            elapsed = time.perf_counter() - t0
            print(f"[moa-bench] completed in {elapsed:.1f}s")

            # The response is already OpenAI-format — serialize it
            self._json_response(200, response)

        except Exception as exc:
            elapsed = time.perf_counter() - t0
            print(f"[moa-bench] ERROR after {elapsed:.1f}s: {exc}")
            self._json_response(500, {"error": {"message": str(exc)}})

    def _handle_stream(self, messages, temperature, max_tokens, tools, extra, t0):
        """Streaming: call the real MoA facade (non-streaming) and emit the
        result as SSE chunks for spark_bench's streaming client.

        MoAChatCompletions.create() always returns a complete ChatCompletion
        object — it does not produce a real streaming iterator. So we call it
        non-streaming, then synthesize SSE chunks from the full response so
        spark_bench's urllib streaming parser can consume it.
        """
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        try:
            api_kwargs = {
                "messages": messages,
                "temperature": temperature,
            }
            if max_tokens is not None:
                api_kwargs["max_tokens"] = max_tokens
            if tools:
                api_kwargs["tools"] = tools
                api_kwargs["tool_choice"] = "auto"
            api_kwargs.update(extra)

            # Always call non-streaming — the facade returns a complete response
            response = _FACADE.create(**api_kwargs)

            # Normalize to dict
            if hasattr(response, "model_dump"):
                resp_dict = response.model_dump()
            elif hasattr(response, "to_dict"):
                resp_dict = response.to_dict()
            elif isinstance(response, dict):
                resp_dict = response
            else:
                resp_dict = json.loads(str(response))

            # Emit the content as a single SSE chunk (simulating streaming)
            choice = resp_dict.get("choices", [{}])[0]
            msg = choice.get("message", {})
            content = msg.get("content") or ""
            reasoning = msg.get("reasoning") or msg.get("reasoning_content") or ""
            tool_calls = msg.get("tool_calls") or []
            usage = resp_dict.get("usage", {})
            finish = choice.get("finish_reason", "stop")

            # Build a single chunk with the full content
            chunk = {
                "id": resp_dict.get("id", f"chatcmpl-moa-{int(time.time())}"),
                "object": "chat.completion.chunk",
                "created": resp_dict.get("created", int(time.time())),
                "model": "moa-local",
                "choices": [{
                    "index": 0,
                    "delta": {
                        "role": "assistant",
                        "content": content,
                        **({"reasoning": reasoning} if reasoning else {}),
                        **({"tool_calls": tool_calls} if tool_calls else {}),
                    },
                    "finish_reason": None,
                }],
            }
            self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode("utf-8"))
            self.wfile.flush()

            # Final chunk with finish_reason + usage
            final_chunk = {
                "id": chunk["id"],
                "object": "chat.completion.chunk",
                "created": chunk["created"],
                "model": "moa-local",
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": finish,
                }],
                "usage": usage,
            }
            self.wfile.write(f"data: {json.dumps(final_chunk)}\n\n".encode("utf-8"))
            self.wfile.flush()

            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()

            elapsed = time.perf_counter() - t0
            print(f"[moa-bench] stream completed in {elapsed:.1f}s, {len(content)} chars")

        except Exception as exc:
            elapsed = time.perf_counter() - t0
            print(f"[moa-bench] STREAM ERROR after {elapsed:.1f}s: {exc}")
            error_chunk = {"error": {"message": f"MOA stream error: {exc}"}}
            self.wfile.write(f"data: {json.dumps(error_chunk)}\n\n".encode("utf-8"))
            self.wfile.flush()

    def _json_response(self, code, data):
        # Handle objects that aren't plain dicts (OpenAI response objects)
        if hasattr(data, "model_dump"):
            data = data.model_dump()
        elif hasattr(data, "to_dict"):
            data = data.to_dict()
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    p = argparse.ArgumentParser(description="Hermes MOA Benchmark Proxy")
    p.add_argument("--port", type=int, default=8890, help="port to listen on")
    p.add_argument("--host", default="0.0.0.0", help="host to bind")
    args = p.parse_args()

    global _FACADE
    print(f"[moa-bench] Initializing Hermes MOA facade from {HERMES_HOME}...")
    _FACADE = _load_moa_facade()
    print(f"[moa-bench] Facade ready")

    print(f"[moa-bench] Starting proxy on {args.host}:{args.port}")
    print(f"[moa-bench] Endpoint: http://localhost:{args.port}/v1/chat/completions")
    print(f"[moa-bench] Model name for spark_bench: moa-local")

    server = ThreadingHTTPServer((args.host, args.port), MOAHandler)
    print(f"[moa-bench] Server is threaded (concurrent requests OK)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[moa-bench] Shutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
