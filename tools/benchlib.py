"""Shared helpers for the ~/bench suite: HTTP client, timing, provenance.

Reconstructed 2026-10-07. The original benchlib.py was lost with ~/bench; this
reimplements the pieces the T20 runner needs from the documented behavior.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request

# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def _req(port: int, path: str, body: dict | None, timeout: int = 1800):
    url = f"http://127.0.0.1:{port}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def chat(
    port: int,
    prompt: str,
    max_tokens: int = 256,
    temperature: float = 0.2,
    cache_prompt: bool = True,
    **extra,
) -> dict:
    """One chat turn. Returns {content, prompt_n, completion_n, pp_tps, tg_tps, finish, raw}."""
    body = {
        "model": "local",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
        "cache_prompt": cache_prompt,
    }
    body.update(extra)
    t0 = time.time()
    raw = _req(port, "/v1/chat/completions", body)
    wall = time.time() - t0
    ch = raw["choices"][0]
    msg = ch["message"]
    usage = raw.get("usage", {})
    timings = raw.get("timings", {})
    return {
        "content": (msg.get("content") or "").strip(),
        "reasoning": msg.get("reasoning_content") or "",
        "prompt_n": usage.get("prompt_tokens"),
        "completion_n": usage.get("completion_tokens"),
        "pp_tps": timings.get("prompt_per_second"),
        "tg_tps": timings.get("predicted_per_second"),
        "finish": ch.get("finish_reason"),
        "wall": wall,
        "raw": raw,
    }


def model_info(port: int) -> dict:
    """Model id, n_ctx, n_ctx_train, n_params, ftype from /v1/models."""
    d = _req(port, "/v1/models", None)
    m = d["data"][0]
    meta = m.get("meta", {})
    return {
        "id": m.get("id"),
        "n_ctx": meta.get("n_ctx"),
        "n_ctx_train": meta.get("n_ctx_train"),
        "n_params": meta.get("n_params"),
        "ftype": meta.get("ftype"),
    }


# ---------------------------------------------------------------------------
# Build provenance: which llama.cpp build serves a port, from /proc/<pid>/maps
# ---------------------------------------------------------------------------

def server_pid(port: int) -> int | None:
    """PID of the llama-server listening on `port` (from /proc, no ss needed)."""
    try:
        out = subprocess.run(
            ["ss", "-tlnp"], capture_output=True, text=True, timeout=10
        ).stdout
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    for line in out.splitlines():
        if f":{port}" not in line:
            continue
        m = re.search(r"pid=(\d+)", line)
        if m:
            return int(m.group(1))
    return None


def build_provenance(port: int) -> str:
    """The libggml-vulkan.so path of the serving build — names the build tree."""
    pid = server_pid(port)
    if not pid:
        return "unknown"
    try:
        with open(f"/proc/{pid}/maps") as f:
            for line in f:
                if "libggml-vulkan.so" in line and "/" in line:
                    return line.split()[-1].strip()
    except OSError:
        pass
    return "unknown"


def build_identity(port: int) -> dict:
    """Full llama.cpp build identity of the server listening on `port`.

    Why this exists: `build_provenance` names the tree by its libggml path, which
    cannot distinguish a re-measure after a `git pull` from the original run — the
    path is identical, the code is not. Three independent facts are recorded here:
      * build_info  from /props  — the server's own string, e.g. "b3-1a33095"
      * build_commit from the tree's git HEAD — survives a stale /props
      * build_version from `llama-server --version` — human-readable provenance
    Any of the three may be missing (hosted shim ports, tree not a git checkout);
    a None is honest, an invented value is not.
    """
    ident = {
        "build_so": None,
        "build_tree": None,
        "build_abi": None,
        "build_info": None,
        "build_commit": None,
        "build_dirty": None,
        "build_version": None,
    }
    so = build_provenance(port)
    if so and so != "unknown":
        ident["build_so"] = so
        m = re.search(r"\.so\.(\S+)$", os.path.basename(so))
        if m:
            ident["build_abi"] = m.group(1)
        if "/build/" in so:
            tree = so.split("/build/")[0]
            ident["build_tree"] = os.path.basename(tree)
            if os.path.isdir(os.path.join(tree, ".git")):
                try:
                    ident["build_commit"] = subprocess.run(
                        ["git", "-C", tree, "rev-parse", "--short=9", "HEAD"],
                        capture_output=True, text=True, timeout=10,
                    ).stdout.strip() or None
                    dirty = subprocess.run(
                        ["git", "-C", tree, "status", "--porcelain", "--untracked-files=no"],
                        capture_output=True, text=True, timeout=15,
                    ).stdout.strip()
                    ident["build_dirty"] = bool(dirty)
                except (OSError, subprocess.SubprocessError):
                    pass
            binary = os.path.join(tree, "build", "bin", "llama-server")
            if os.path.isfile(binary):
                try:
                    out = subprocess.run(
                        [binary, "--version"], capture_output=True, text=True, timeout=20
                    )
                    text = (out.stdout or "") + (out.stderr or "")
                    first = next(
                        (ln.strip() for ln in text.splitlines() if ln.strip().startswith("version:")),
                        "",
                    ) or (text.splitlines()[0].strip() if text.strip() else "")
                    ident["build_version"] = first or None
                except (OSError, subprocess.SubprocessError):
                    pass
    try:
        props = _req(port, "/props", None)
        ident["build_info"] = props.get("build_info") or None
    except Exception:
        pass
    if ident["build_info"] is None and ident["build_version"]:
        m = re.search(r"commit ([0-9a-f]{7,})", ident["build_version"])
        b = re.search(r"build (\d+)", ident["build_version"])
        if m:
            ident["build_info"] = f"b{b.group(1)}-{m.group(1)}" if b else m.group(1)
    return ident


def env_provenance() -> dict:
    """Kernel/OS provenance for a run: a build-provenance-equivalent for the platform.

    Why this exists: the September 2026 rows on the reference host were taken on a DIFFERENT
    installation (the box was reinstalled 2026-10-04 — pacman.log starts with a calamares
    sysroot run), so they differ in kernel, Mesa/RADV and llama.cpp build all at once. The
    kernel/Mesa axes matter for load time, GTT/residency and any disk-streaming decode path
    (e.g. Qwen3.8-Flash-Next's --lazy-mode auto PLE tables); they should not move a warm,
    fully-resident model's steady-state tg/pp. Record them per run so a future "why did this
    number move" question is answerable from the run file rather than from memory.
    """
    import glob
    import platform
    import subprocess

    out = {"kernel": platform.release()}
    try:
        out["boot_id"] = open("/proc/sys/kernel/random/boot_id").read().strip()
    except OSError:
        pass
    try:
        for line in open("/proc/stat"):
            if line.startswith("btime"):
                out["boot_epoch"] = int(line.split()[1])
                break
    except OSError:
        pass
    # GPU-addressable pool: this is the number that actually gates model residency
    for pat in ("/sys/class/drm/card*/device/mem_info_gtt_total",
                "/sys/class/drm/card*/device/mem_info_vram_total"):
        for p in sorted(glob.glob(pat)):
            try:
                key = "gtt_total_gib" if "gtt" in p else "vram_total_gib"
                out[key] = round(int(open(p).read().strip()) / 2**30, 1)
            except (OSError, ValueError):
                pass
    try:
        out["ttm_pages_limit"] = open("/sys/module/ttm/parameters/pages_limit").read().strip()
    except OSError:
        pass
    # userspace GPU stack, best effort — pacman is CachyOS-specific and may be absent
    try:
        q = subprocess.run(["pacman", "-Q", "mesa", "vulkan-radeon", "llvm"],
                           capture_output=True, text=True, timeout=10)
        if q.returncode == 0:
            out["gpu_stack"] = " ".join(q.stdout.split())
    except (OSError, subprocess.SubprocessError):
        pass
    return out


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def contains_any(content: str, accepts: list[str]) -> bool:
    low = content.lower()
    return any(a.lower() in low for a in accepts)


def last_number(content: str) -> str | None:
    """The last number token in the text (numeric answers read in answer position)."""
    nums = re.findall(r"-?\d+(?:\.\d+)?", content)
    return nums[-1] if nums else None
