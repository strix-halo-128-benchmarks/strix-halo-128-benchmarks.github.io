#!/usr/bin/env python3
"""Generate leaderboards.md — one page of per-axis rankings, from the report's own matrix.

Design rules, all of which exist because the report argues for them:

  * every row carries its cap, its item count, its build and its measured date — a bare score is the
    artefact this project refuses to publish;
  * a score measured at a smaller cap is marked `floor` and never ranked as equal to a ceiling;
  * no composite index. There is no single number, and inventing one here would undo §9;
  * retired models stay in the tables, marked `✗`, because a leaderboard with the losers deleted is
    how you end up re-downloading them.

Parsed from the published matrix (Table 4) rather than recomputed, so the leaderboards cannot disagree
with the report: one source, two views.

usage: leaderboards.py <strix-halo-llm-testing.md> <leaderboards.md>
"""
from __future__ import annotations

import re
import sys

CAP_STANDARD = 2048
CAP_LARGE = 4096


def parse_matrix(path: str) -> list[dict]:
    txt = open(path, encoding="utf-8").read()
    block = re.search(r"\| Model \| Params \| Quant \| HumanEval.*?\n\n", txt, re.S)
    if not block:
        sys.exit("no matrix found — did Table 4 change shape?")
    rows = []
    for line in block.group(0).splitlines():
        if not line.startswith("|") or line.startswith("| Model") or set(line) <= set("|-: "):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 11:
            continue
        status = c[10]
        rows.append({
            "model": c[0], "params": c[1], "quant": c[2],
            "he": c[3], "mmlu": c[4], "riddles": c[5],
            "prefill": c[6], "decode": c[7],
            "measured": c[8], "build": c[9], "status": status,
            "retired": "✗" in status,
            "role": ("driver" if "driver" in status else "boot" if "boot" in status else ""),
        })
    return rows


def score(cell: str):
    """'0.9573 (164@2048)' -> (0.9573, 164, 2048); 'invalid …' / '—' -> None."""
    m = re.match(r"(0\.\d+)\s*\((\d+)(?:@(\d+))?\)", cell)
    if not m:
        return None
    return float(m.group(1)), int(m.group(2)), (int(m.group(3)) if m.group(3) else None)


def riddle(cell: str):
    m = re.match(r"(\d+)\s*/\s*(\d+)", cell)
    return (int(m.group(1)), int(m.group(2))) if m else None


def num(cell: str):
    m = re.match(r"([\d.]+)", cell)
    return float(m.group(1)) if m else None


def status_label(r: dict) -> str:
    if r["retired"]:
        return "✗ retired"
    if r["role"] == "driver":
        return "✓ driver"
    if r["role"] == "boot":
        return "✓ boot"
    return "✓"


def flag_cap(cap) -> str:
    """Name the cap discipline in the cell itself."""
    if cap is None:
        return ""
    if cap < CAP_STANDARD:
        return " **floor**"
    if cap > CAP_LARGE:
        return " (above standard cap)"
    return ""


def table(rows, value_fn, header, sort_key, floor_note_threshold=None):
    """Render one ranked table. Rows keep cap/n/build/date so nothing is quotable on its own."""
    got = []
    for r in rows:
        v = value_fn(r)
        if v is None:
            continue
        got.append((r, v))
    got.sort(key=sort_key, reverse=True)
    out = [f"| # | model | {header} | n | cap | build | measured | status |",
           "|---:|---|---:|---:|---:|---|---|---|"]
    for i, (r, v) in enumerate(got, 1):
        if header == "HumanEval" or header == "MMLU-Pro":
            s, n, cap = v
            cell = f"{s:.4f}{flag_cap(cap)}"
            out.append(f"| {i} | {r['model']} | {cell} | {n} | {cap or '—'} | {r['build']} | {r['measured']} | {status_label(r)} |")
        else:
            cell = v
            out.append(f"| {i} | {r['model']} | {cell} | — | — | {r['build']} | {r['measured']} | {status_label(r)} |")
    return "\n".join(out), [r["model"] for r, _ in got]


def main() -> None:
    src, dst = sys.argv[1], sys.argv[2]
    rows = parse_matrix(src)

    def he(r):
        v = score(r["he"])
        return v if v and v[2] and v[2] >= CAP_STANDARD else None

    def small_he(r):
        v = score(r["he"])
        return v if v and v[2] and v[2] < CAP_STANDARD else None

    def mmlu(r):
        v = score(r["mmlu"])
        return v if v and v[2] and v[2] >= CAP_STANDARD else None

    def rid(r):
        v = riddle(r["riddles"])
        return f"{v[0]}/{v[1]}" if v else None

    def dec(r):
        v = num(r["decode"])
        return f"{v:.1f} t/s" if v else None

    def pre(r):
        v = num(r["prefill"])
        return f"{v:.0f} t/s" if v else None

    code_tbl, code_models = table(rows, he, "HumanEval", lambda x: (x[1][0], x[1][2]))
    floor_tbl, floor_models = table(rows, small_he, "HumanEval", lambda x: (x[1][0], x[1][1]))
    know_tbl, _ = table(rows, mmlu, "MMLU-Pro", lambda x: (x[1][0], x[1][2]))
    rid_tbl, _ = table(rows, rid, "riddles", lambda x: riddle(x[1]) if riddle(x[1]) else (0, 0))
    dec_tbl, _ = table(rows, dec, "decode", lambda x: float(x[1].split()[0]))
    pre_tbl, _ = table(rows, pre, "prefill", lambda x: float(x[1].split()[0]))

    n_rows = len(rows)
    n_live = sum(1 for r in rows if not r["retired"])
    doc = f"""# Leaderboards, by axis

Every number here comes from the same matrix as the report, with the same rules. Ranked on one axis at a
time, because there is no composite score and this project does not publish one — a model that wins code
and loses knowledge is not "0.7 of a model".

**Three things to read before the first table.**

1. **The cap is part of the score.** A row measured at 2048 or 4096 tokens per answer is only comparable
   inside that band. Anything measured below 2048 is marked **floor** and ranked in its own table at the
   bottom, never against a ceiling.
2. **`n` is the item count, not a formality.** HumanEval is out of 164, MMLU-Pro out of 120. A row at a
   smaller n is plumbing and says so.
3. **`build` is the llama.cpp that produced the row.** Decode rates move 10-20% between builds, so a
   throughput comparison across different builds is a comparison of builds as much as models.

{n_rows} measured rows: **{n_live} servable**, {n_rows - n_live} retired but kept in place, because a
leaderboard with the failures deleted is how the same 60 GB gets downloaded twice.

---

## Code — HumanEval, 164 items

{code_tbl}

The driver is `gemma4-26b-uncen` — 15.6 GiB, 56.9 t/s, and still the best coder on the box. The three
largest models here (122B, 120B) sit below it on code while running 2-2.5× slower: size buys knowledge
fidelity on this platform, not code.

## Knowledge — MMLU-Pro, 120 items, chat 0-shot

{know_tbl}

The 26B MoE also leads knowledge. The two 120B-class models recover some ground here and none of it
justifies 60-70 GiB at 23-27 t/s on a box whose best model fits in a sixth of that.

## Reasoning traps — riddles and arithmetic, 14 items

{rid_tbl}

Fourteen hand-written riddles and three arithmetic traps. Not a benchmark in the psychometric sense: it
catches a model that pattern-matches an answer without following the question, which is exactly the
failure the code and knowledge axes do not show. `14/14` is the ceiling; several strong coders score
10-11 because they answer confidently and wrongly.

## Speed — decode tokens/second

{dec_tbl}

Decode is bandwidth-bound on this platform (~256 GB/s shared with the CPU), so it tracks active
parameters, not total parameters. The top of this table is two ~12-24B MoEs; the bottom is a 120B.

## Prefill — prompt tokens/second

{pre_tbl}

Prefill is shader-bound and moves far more between builds than decode does. Use it to size long-prompt
work, not to rank models generally.

---

## Floors — HumanEval measured below the 2048-token standard

{floor_tbl}

These rows exist because a floor is still information: it is the lowest a model is known to score. They
are not ranked against the tables above, and a plan that depends on one of them should re-measure first.

---

## What is deliberately missing

- **No composite index.** Weighting code, knowledge and speed into one number requires assumptions this
  project will not make on the reader's behalf.
- **No context-window ranking.** Native context is a property of the file, not a measurement; the report
  covers it per model, including the 1,048,576-token Kimi row and why it is measured at 65536.
- **No per-watt axis yet.** Power is measured (§15) but not paired with throughput per model, so any
  efficiency ranking here would be invented.

*Source, data and build scripts: [github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io](https://github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io).
Full report and caveats: [index.html](index.html) · deleted models and restore recipes:
[retired-models.html](retired-models.html).*
"""
    open(dst, "w", encoding="utf-8").write(doc)
    print(f"   {len(doc)} bytes · code {len(code_models)} · floors {len(floor_models)} · rows {n_rows}")


if __name__ == "__main__":
    main()
