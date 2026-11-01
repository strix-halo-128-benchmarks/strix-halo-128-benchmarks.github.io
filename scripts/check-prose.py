#!/usr/bin/env python3
"""Gate: every score quoted in the report's prose must exist in its own matrix.

The failure this exists to catch is real and happened here: §9.1 said `nemotron-super-120b` scores 0.9329
while the matrix and the errata in §21 both said 0.9512 — a document contradicting its own correction. Prose
copies drift because the table is generated and the sentence is not.

Rules, deliberately conservative so it does not cry wolf:
  * only four-decimal values of the form 0.xxxx are checked (the shape every capability score takes);
  * a value passes if it appears anywhere in Table 4's capability cells, or in the change-log page;
  * §21 and §22 are excluded here — they quote superseded numbers on purpose;
  * percentages, latencies and throughputs are not checked: they are not sampling-fragile the same way.

usage: check-prose.py <report.md> <changelog.md> [runs_dir]
exit 1 on any unaccounted score, printing the line.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys


def matrix_scores(report: str) -> set[str]:
    block = re.search(r"\| Model \| Params \| Quant \| HumanEval.*?\n\n", report, re.S)
    if not block:
        sys.exit("check-prose: no matrix found — did Table 4 change shape?")
    return set(re.findall(r"0\.\d{4}", block.group(0)))


def prose_scores(report: str) -> list[tuple[int, str, str]]:
    """Scores outside the matrix tables, excluding the change log (which quotes history on purpose)."""
    out = []
    stop = report.find("## 21. Change log")
    body = report[:stop] if stop > 0 else report
    in_table = False
    for i, line in enumerate(body.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("|"):
            in_table = True
            continue
        if in_table and not stripped:
            in_table = False
        if in_table:
            continue
        for m in re.finditer(r"0\.\d{4}", line):
            out.append((i, m.group(0), stripped[:110]))
    return out


def archive_scores(runs_dir: str) -> set[str]:
    """Every four-decimal value the raw run archive contains — the honest test of 'traceable to a run'.

    Table 4 alone is not enough: it holds only the rows that completed the suite, and a legitimate number for
    an excluded model (qwen38fn-abl's poisoned MMLU, an IFEval subset, a retired file, a hosted probe) would
    otherwise look invented. Values are rounded to four places because that is how they are quoted.
    """
    out: set[str] = set()
    paths = (glob.glob(os.path.join(runs_dir, "**", "*.jsonl"), recursive=True)
             + glob.glob(os.path.expanduser("~/bench/runs/*.jsonl"))
             + glob.glob(os.path.expanduser("~/bench/api-calls.jsonl")))
    for path in paths:
        for line in open(path, encoding="utf-8", errors="replace"):
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue

            def walk(v):
                if isinstance(v, bool):
                    return
                if isinstance(v, str):
                    try:
                        v = float(v)
                    except ValueError:
                        return
                if isinstance(v, (int, float)) and 0 <= v < 1:
                    out.add(f"{v:.4f}")
                elif isinstance(v, dict):
                    for x in v.values():
                        walk(x)
                elif isinstance(v, list):
                    for x in v:
                        walk(x)
            walk(row)
    return out


def pair_check(report: str) -> list[str]:
    """The narrow rule that matters: 'X code, Y MMLU/knowledge' in a model's own §9.1 paragraph must equal
    that model's row in Table 4.

    This is the failure that actually happened: the paragraph for nemotron-super-120b said 0.9329 while its
    row said 0.9512. Both numbers were real measurements (153/164 and 156/164), so a "does this value exist
    anywhere" check cannot catch it — only comparing the sentence against that model's own row can.
    """
    block = re.search(r"\| Model \| Params \| Quant \| HumanEval.*?\n\n", report, re.S)
    if not block:
        return []
    rows = {}
    for line in block.group(0).splitlines():
        if not line.startswith("| ") or line.startswith("| Model") or set(line) <= set("|-: "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 5:
            rows[cells[0]] = cells
    problems = []
    for para in re.split(r"\n\s*\n", report):
        m = re.match(r"\*\*([^*]+)", para.strip())
        if not m:
            continue
        name = m.group(1).lower()
        row = next((v for k, v in rows.items() if k.lower() in name or name.startswith(k.lower())), None)
        if not row:
            continue
        pair = re.search(r"([01]\.\d{3,4})\s+code,?\s+([01]\.\d{3,4})\s+(?:MMLU|knowledge)", para)
        if not pair:
            continue
        want_he, want_mm = pair.group(1), pair.group(2)
        if want_he not in row[3]:
            problems.append(f"{row[0]}: paragraph says {want_he} code, row says {row[3]}")
        if want_mm not in row[4]:
            problems.append(f"{row[0]}: paragraph says {want_mm} knowledge, row says {row[4]}")
    return problems


def main() -> None:
    report = open(sys.argv[1], encoding="utf-8").read()
    changelog = open(sys.argv[2], encoding="utf-8").read() if len(sys.argv) > 2 else ""
    runs_dir = sys.argv[3] if len(sys.argv) > 3 else os.path.expanduser("~/runs")
    allow_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prose-allowlist.txt")
    allowed: set[str] = set()
    if os.path.exists(allow_path):
        for line in open(allow_path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#"):
                allowed.add(line.split()[0])
    known = matrix_scores(report) | archive_scores(runs_dir) | allowed
    history = set(re.findall(r"0\.\d{4}", changelog))
    bad = [(i, v, l) for i, v, l in prose_scores(report) if v not in known and v not in history]
    pairs = pair_check(report)
    if pairs:
        print(f"   FAIL: {len(pairs)} prose/row mismatch(es) — the sentence disagrees with the model's own row")
        for p in pairs[:10]:
            print(f"     {p}")
        sys.exit(1)
    checked = len(prose_scores(report))
    if bad:
        print(f"   FAIL: {len(bad)} prose score(s) not present in the matrix or the change log")
        for i, v, l in bad[:12]:
            print(f"     line {i}: {v}  {l}")
        sys.exit(1)
    print(f"   ok: {checked} prose scores, all traceable to the matrix, the archive or the allowlist "
          f"({len(allowed)} historical values)")


if __name__ == "__main__":
    main()
