#!/usr/bin/env python3
"""Context-scaling curve for a resident llama.cpp server.

Runs the harness's own needle probe at increasing context sizes against whatever is already
serving on the port — no model load, no unit change — and records per point: the prompt length
the server actually saw, whether the needle was retrieved, wall time, and the prefill/decode
rates llama.cpp reports in its own timings.

The point is the shape, not one number: a model fine at 8k can fall over at 32k, which is why
the report's open-items list has said since the kernel move that no 32k needle had been run.

  usage: ctxcurve.py --port 8100 --sizes 2000,8000,32000,128000 [--tag ctxcurve-driver]
"""
from __future__ import annotations

import argparse
import json
import os
import time

import checks
import benchlib as bl


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--sizes", default="2000,8000,32000,128000")
    ap.add_argument("--tag", default="ctxcurve")
    ap.add_argument("--max-tokens", type=int, default=256)
    args = ap.parse_args()

    props = bl._req(args.port, "/props", None) or {}
    model = (props.get("model_path") or "?").split("/")[-1]
    n_ctx = (props.get("default_generation_settings") or {}).get("n_ctx")
    rows = []
    print(f"port {args.port} · {model} · ctx {n_ctx}")
    print(f"{'target':>7} {'prompt_n':>9} {'pass':>5} {'wall_s':>7} {'pp t/s':>8} {'tg t/s':>7}")

    for size in [int(s) for s in args.sizes.split(",") if s.strip()]:
        t0 = time.time()
        r = checks.needle(args.port, ctx_tokens=size, max_tokens=args.max_tokens)
        wall = time.time() - t0
        row = {
            "size_target": size,
            "prompt_n": r.get("prompt_n"),
            "pass": r["pass"],
            "finish": r["finish"],
            "retried": r["retried"],
            "completion_n": r.get("completion_n"),
            "wall_s": round(wall, 1),
            "pp_tps": round(r["pp_tps"], 1) if r.get("pp_tps") else None,
            "tg_tps": round(r["tg_tps"], 2) if r.get("tg_tps") else None,
            "model": model,
            "n_ctx": n_ctx,
        }
        rows.append(row)
        print(f"{size:>7} {str(row['prompt_n']):>9} {str(row['pass']):>5} {wall:>7.1f} "
              f"{str(row['pp_tps'] or '-'):>8} {str(row['tg_tps'] or '-'):>7}")

    out = os.path.expanduser(f"~/runs/{args.tag}.jsonl")
    with open(out, "a") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
