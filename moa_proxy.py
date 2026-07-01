#!/usr/bin/env python3
"""
MOA Proxy Server — exposes the 3-model Mixture-of-Agents pipeline as an
OpenAI-compatible /v1/chat/completions endpoint for spark_bench.

Pipeline per request:
  1. Fan out to Qwen 3.6 35B (reference) + Qwopus 3.6 27B (reference) in parallel
  2. Feed both reference outputs to DeepSeek V4 Flash (aggregator)
  3. Stream the aggregator's response back to the caller

Usage:
  python3 moa_proxy.py --port 8890

  # Then run spark_bench against it:
  ./spark_bench.py eval \
    --label moa-3local-v5c \
    --endpoint http://localhost:8890/v1 \
    --model moa-local \
    --thinking off --repeats 2 \
    --tier all --gen-tokens 256 --timeout 1200
"""

import argparse
import json
import time
import threading
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

# ── Model endpoints ──────────────────────────────────────────────────
REFERENCE_MODELS = [
    {
        "name": "qwen3.6-35b-a3b-nvfp4",
        "endpoint": "http://10.0.0.120:8000/v1",
        "label": "Qwen 3.6 35B (b610)",
    },
    {
        "name": "qwopus3.6-27b-mtp",
        "endpoint": "http://10.0.0.183:8000/v1",
        "label": "Qwopus 3.6 27B (366f)",
    },
]
AGGREGATOR = {
    "name": "deepseek-v4-flash-dspark",
    "endpoint": "http://10.0.0.109:8888/v1",
    "label": "DeepSeek V4 Flash (dual-spark)",
}

REFERENCE_TEMP = 0.6
AGGREGATOR_TEMP = 0.4
REFERENCE_MAX_TOKENS = 2048
AGGREGATOR_MAX_TOKENS = 8192


def _call_model(endpoint, model, messages, max_tokens, temperature, timeout=600):
    """Non-streaming call to a reference model. Returns (text, reasoning, usage)."""
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }
    url = endpoint.rstrip("/") + "/chat/completions"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer none"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        choice = data.get("choices", [{}])[0].get("message", {})
        text = choice.get("content") or ""
        reasoning = choice.get("reasoning") or choice.get("reasoning_content") or ""
        usage = data.get("usage", {})
        return text, reasoning, usage
    except Exception as exc:
        return f"[reference model error: {exc}]", "", {}


def _call_reference(slot, messages):
    """Call one reference model, return (label, text)."""
    text, reasoning, usage = _call_model(
        slot["endpoint"], slot["name"], messages,
        REFERENCE_MAX_TOKENS, REFERENCE_TEMP,
    )
    return slot["label"], text


def _run_references_parallel(messages):
    """Fan out to all reference models in parallel. Returns list of (label, text)."""
    results = [None] * len(REFERENCE_MODELS)
    threads = []

    def worker(idx, slot):
        results[idx] = _call_reference(slot, messages)

    for i, slot in enumerate(REFERENCE_MODELS):
        t = threading.Thread(target=worker, args=(i, slot))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    return results


def _build_aggregator_messages(original_messages, reference_outputs):
    """Build the message list for the aggregator: system prompt + refs + original."""
    ref_text = "\n\n".join(
        f"--- {label} ---\n{text}" for label, text in reference_outputs if text
    )
    aggregator_system = (
        "You are the aggregator in a Mixture of Agents process. Synthesize the "
        "reference responses below into a single, high-quality answer. "
        "Do not mention the reference models. Provide your best response directly.\n\n"
        f"[Mixture of Agents context — use this as private guidance]\n\n"
        f"References:\n{ref_text}\n\n"
        f"[End of references. Answer the user's request directly now.]"
    )

    # Replace or prepend the system message
    messages = list(original_messages)
    if messages and messages[0].get("role") == "system":
        messages[0] = {
            "role": "system",
            "content": messages[0]["content"] + "\n\n" + aggregator_system,
        }
    else:
        messages.insert(0, {"role": "system", "content": aggregator_system})
    return messages


def _stream_aggregator(endpoint, model, messages, max_tokens, temperature, timeout=1200):
    """Stream from the aggregator. Yields SSE chunks in OpenAI format."""
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    url = endpoint.rstrip("/") + "/chat/completions"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer none"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        for raw in resp:
            line = raw.decode("utf-8", "replace").strip()
            if not line:
                continue
            if line.startswith("data:"):
                data = line[5:].strip()
                if data == "[DONE]":
                    yield "data: [DONE]\n\n"
                    return
                try:
                    obj = json.loads(data)
                    yield f"data: {json.dumps(obj)}\n\n"
                except json.JSONDecodeError:
                    continue


class MOAHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Minimal logging
        print(f"[moa-proxy] {args[0]}")

    def do_GET(self):
        if self.path == "/v1/models":
            models = {
                "object": "list",
                "data": [
                    {
                        "id": "moa-local",
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "moa-proxy",
                    }
                ],
            }
            self._json_response(200, models)
        elif self.path == "/health":
            self._json_response(200, {"status": "ok"})
        else:
            self._json_response(404, {"error": "not found"})

    def do_POST(self):
        if not self.path.startswith("/v1/chat/completions"):
            self._json_response(404, {"error": "not found"})
            return

        # Parse request body
        content_len = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_len).decode("utf-8"))

        messages = body.get("messages", [])
        model = body.get("model", "moa-local")
        stream = body.get("stream", False)
        max_tokens = body.get("max_tokens", AGGREGATOR_MAX_TOKENS)
        temperature = body.get("temperature", AGGREGATOR_TEMP)
        tools = body.get("tools")

        t0 = time.perf_counter()

        # Step 1: Fan out to reference models
        print(f"[moa-proxy] fanning out to {len(REFERENCE_MODELS)} references...")
        ref_outputs = _run_references_parallel(messages)
        for label, text in ref_outputs:
            print(f"[moa-proxy]   {label}: {len(text)} chars")
        ref_elapsed = time.perf_counter() - t0
        print(f"[moa-proxy] references done in {ref_elapsed:.1f}s")

        # Step 2: Build aggregator prompt and stream response
        agg_messages = _build_aggregator_messages(messages, ref_outputs)

        # If tools are provided, pass them through to the aggregator
        extra_body = {}
        if tools:
            extra_body["tools"] = tools
            extra_body["tool_choice"] = "auto"

        # Pass through chat_template_kwargs if present (for thinking on/off)
        if "chat_template_kwargs" in body:
            extra_body["chat_template_kwargs"] = body["chat_template_kwargs"]

        if stream:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()

            try:
                for chunk in _stream_aggregator(
                    AGGREGATOR["endpoint"], AGGREGATOR["name"],
                    agg_messages, max_tokens, temperature,
                ):
                    self.wfile.write(chunk.encode("utf-8"))
                    self.wfile.flush()
            except Exception as exc:
                error_chunk = {
                    "error": {"message": f"aggregator stream error: {exc}"}
                }
                self.wfile.write(f"data: {json.dumps(error_chunk)}\n\n".encode())
                self.wfile.flush()
        else:
            # Non-streaming: collect and return
            text, reasoning, usage = _call_model(
                AGGREGATOR["endpoint"], AGGREGATOR["name"],
                agg_messages, max_tokens, temperature,
                timeout=1200,
            )
            total = time.perf_counter() - t0
            print(f"[moa-proxy] total: {total:.1f}s, response: {len(text)} chars")

            response = {
                "id": f"chatcmpl-moa-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "moa-local",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": text,
                            "reasoning": reasoning,
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": usage,
            }
            self._json_response(200, response)

    def _json_response(self, code, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    p = argparse.ArgumentParser(description="MOA Proxy Server")
    p.add_argument("--port", type=int, default=8890, help="port to listen on")
    p.add_argument("--host", default="0.0.0.0", help="host to bind")
    args = p.parse_args()

    print(f"[moa-proxy] Starting MOA proxy on {args.host}:{args.port}")
    print(f"[moa-proxy] References: {', '.join(r['label'] for r in REFERENCE_MODELS)}")
    print(f"[moa-proxy] Aggregator: {AGGREGATOR['label']}")
    print(f"[moa-proxy] Endpoint: http://localhost:{args.port}/v1/chat/completions")

    server = HTTPServer((args.host, args.port), MOAHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[moa-proxy] Shutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
