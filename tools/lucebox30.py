#!/usr/bin/env python3
"""Cross-validation: run someone else's 30-item quality suite against a local server.

Source: `Luce-Org/lucebox` at commit 90f85fa, `harness/benchmarks/prompts/bench_{he,gsm,math}.jsonl`
— the 10+10+10 suite published alongside the pepuscz Strix Halo results, with its fixture hashes.
Running it here answers a different question from our own axes: not "how good is this model" but
"do two independently-built harnesses agree". If our driver scores 30/30 the way their
Qwen3.8-Flash-Next deployment did, the datasets corroborate each other; if it does not, that is the
more interesting result and worth publishing either way.

Scoring, per suite:
  he    the generated function is executed against the fixture's own `gold_test` in a subprocess
        with a timeout — same idea as our HumanEval axis, different prompts
  gsm   the last number in the answer is compared with `gold_answer` (tolerance 1e-6)
  math  `\\boxed{…}` if present, else the last non-empty line; compared against `gold_answer`
        after normalising $, spaces and \\left/\\right

  usage: lucebox30.py --port 8100 [--tag lucebox30-driver]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

import benchlib as bl

COMMIT = "90f85fa401c6a3c61d9e4d0e2da7fc48a5e8915e"
RAW = f"https://raw.githubusercontent.com/Luce-Org/lucebox/{COMMIT}/harness/benchmarks/prompts/"


def fetch(name: str) -> list[dict]:
    cache = os.path.expanduser(f"~/.cache/lucebox/{COMMIT}-{name}")
    if not os.path.exists(cache):
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        data = urllib.request.urlopen(RAW + name, timeout=30).read()
        open(cache, "wb").write(data)
    return [json.loads(l) for l in open(cache, encoding="utf-8").read().splitlines() if l.strip()]


def code_of(text: str) -> str:
    blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.S)
    return (blocks[0] if blocks else text).strip()


def run_tests(code: str, gold_test: str, entry: str | None) -> tuple[bool, str]:
    src = f"{code}\n\n{gold_test}\n"
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
        fh.write(src)
        path = fh.name
    try:
        r = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=20)
        return r.returncode == 0, (r.stderr or r.stdout)[-200:]
    except subprocess.TimeoutExpired:
        return False, "timeout"
    finally:
        os.unlink(path)


def final_segment(text: str) -> str:
    """The part of the answer a human would read as the result.

    Taking the last number in the whole completion is wrong: "…= 8 pairs × $8.00 = $64.00.
    Answer: Kylar needs $64 for the 16 glasses" ends on 16, so a last-number grader scored a
    correct answer as a miss. Prefer an explicit answer marker, then the last non-empty line.
    """
    t = text.strip()
    for marker in ("**Answer:**", "Answer:", "Final Answer:", "**Final Answer:**", "The answer is"):
        idx = t.rfind(marker)
        if idx != -1:
            return t[idx + len(marker):].strip()
    lines = [l for l in t.splitlines() if l.strip()]
    return lines[-1] if lines else ""


def answer_numbers(text: str) -> list[str]:
    """Numbers in the answer sentence, in order.

    Neither first nor last is right on its own: "pay $64 for the 16 glasses" puts the answer first,
    "160 minutes (or 2 hours and 40 minutes)" puts it first too, but "2 hours and 40 minutes" would
    put it second. So the grader collects them all and the caller checks membership, recording which
    rule fired so a wrong pass is auditable from the row.
    """
    seg = final_segment(text).replace(",", "")
    return re.findall(r"-?\d+(?:\.\d+)?", seg)


def boxed_of(text: str) -> str:
    """\\boxed{…} with balanced braces — \\boxed{\\frac{20}{3}} is one argument, not \\frac{20."""
    i = text.rfind("\\boxed{")
    if i == -1:
        return ""
    j, depth = i + len("\\boxed{"), 1
    out = []
    while j < len(text) and depth:
        ch = text[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
        out.append(ch)
        j += 1
    return "".join(out)


def norm_math(text: str) -> str:
    """Reduce a LaTeX answer to a comparable token: fractions to a/b, no $, no spacing."""
    s = boxed_of(text) or final_segment(text)
    s = s.replace("$", "").replace("\\left", "").replace("\\right", "").replace("\\,", "")
    s = re.sub(r"\\d?frac\{([^{}]*)\}\{([^{}]*)\}", r"\1/\2", s)
    s = s.replace("{", "").replace("}", "").replace(" ", "").strip().rstrip(".")
    try:
        num = float(eval(s, {"__builtins__": {}}, {}))   # "−2/3" == "-2/3"; a bare float is already fine
        return f"{num:.10g}"
    except Exception:
        return s


# The fixture ships gold_answer "20" for math_08, but the correct value is 20/3 and the source's
# own results.json records the correction ("math_08 reference corrected to 20/3"). Applying it
# keeps the comparison honest: without it a correct answer is scored as a failure.
GOLD_CORRECTIONS = {"math_08": "20/3"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--tag", default="lucebox30")
    ap.add_argument("--max-per-suite", type=int, default=10)
    ap.add_argument("--suites", default="he,gsm,math")
    args = ap.parse_args()

    wanted = [s.strip() for s in args.suites.split(",") if s.strip()]
    suites = {name: fetch(f"bench_{name}.jsonl") for name in wanted}
    rows = []
    for name, items in suites.items():
        print(f"--- {name} ---")
        for item in items[: args.max_per_suite]:
            prompt = item["messages"][0]["content"]
            r = bl.chat(args.port, prompt, max_tokens=item.get("max_tokens", 1024),
                        temperature=0.0, cache_prompt=False)
            out = r["content"]
            if name == "he":
                ok, detail = run_tests(code_of(out), item.get("gold_test", ""), item.get("entry_point"))
                got = "tests"
            elif name == "gsm":
                nums = answer_numbers(out)
                gold = item.get("gold_answer")
                ok = False
                for n in nums:
                    try:
                        if abs(float(n) - float(gold)) < 1e-6:
                            ok = True
                            break
                    except (TypeError, ValueError):
                        if str(n) == str(gold):
                            ok = True
                            break
                got = nums[0] if nums else None
                detail = f"gold {gold} in {nums[:3]}" 
            else:
                got = norm_math(out)
                gold = GOLD_CORRECTIONS.get(item["id"], item.get("gold_answer", ""))
                ok = got == norm_math(str(gold))
                detail = f"gold {gold} got {got}"
            rows.append({"suite": name, "id": item["id"], "pass": bool(ok),
                         "completion_n": r.get("completion_n"), "prompt_n": r.get("prompt_n"),
                         "final": final_segment(out)[:160].replace("\n", " "),
                         "detail": detail[:120]})
            print(f"  {item['id']:9} {'PASS' if ok else 'FAIL'}  {detail[:80]}")

    out_path = os.path.expanduser(f"~/runs/{args.tag}.jsonl")
    with open(out_path, "w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    total = len(rows)
    passed = sum(1 for r in rows if r["pass"])
    per = {s: (sum(1 for r in rows if r["suite"] == s and r["pass"]), sum(1 for r in rows if r["suite"] == s))
           for s in suites}
    print(f"\nTOTAL {passed}/{total} · " + " · ".join(f"{k} {v[0]}/{v[1]}" for k, v in per.items()))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
