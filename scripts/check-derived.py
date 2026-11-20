#!/usr/bin/env python3
"""Fail the build when the 16 GiB page's prose disagrees with the archive.

    python3 scripts/check-derived.py 16gb-vram.md ~/bench/16gb/matrix.json ~/runs

Every check is a number the page states in prose (a count, an interval, a ratio) recomputed from
`matrix.json` and the newest run row per model and axis. The point is that no assertion about the
tables can go stale without the build saying so: the page has repeatedly carried counts and margins
that were true two revisions earlier.

Checks fall in two kinds:
  PRESENT  the computed value must appear as a string
  ABSENT   a phrase the page used to carry must be gone from the body (history entries exempt)
"""
from __future__ import annotations

import glob
import json
import math
import os
from decimal import Decimal, ROUND_HALF_UP
import re
import sys

FAILS: list[str] = []
PASSES = 0


def ok(name: str, cond: bool, detail: str = "") -> None:
    global PASSES
    if cond:
        PASSES += 1
        print(f"  ok   {name}")
    else:
        FAILS.append(name)
        print(f"  FAIL {name}{(' — ' + detail) if detail else ''}")


def newest_rows(runs_dir: str) -> tuple[dict[tuple[str, str], dict], dict[str, list[dict]]]:
    """Newest row per (model id, axis), joined the way report.py joins them.

    Also returns every riddles row by model, because a riddle cell is cap-dependent: the newest
    row may have been measured at a different riddle cap than the page's stated policy."""
    best: dict[tuple[str, str], dict] = {}
    allrows: dict[tuple[str, str], list[dict]] = {}
    riddles: dict[str, list[dict]] = {}
    for path in glob.glob(os.path.join(runs_dir, "*g16-*.jsonl")):
        base = os.path.basename(path)
        m = re.match(r"\d{8}-\d{6}-g16-(.+)\.jsonl$", base)
        if not m:
            continue
        mid = re.sub(r"-(humaneval|mmlu_pro|mmlu|ifeval|riddles|perf|core|refusal)(-cap\d+)?$", "", m.group(1))
        for line in open(path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            axis = row.get("axis")
            if not axis:
                continue
            key = (mid, axis)
            if key not in best or (row.get("ts") or 0) > (best[key].get("ts") or 0):
                best[key] = row
            allrows.setdefault((mid, axis), []).append(row)
            if axis == "riddles":
                riddles.setdefault(mid, []).append(row)
    return best, allrows


def score(row: dict | None, axis: str) -> tuple[float | None, int | None, int | None]:
    """(value, n, cap) for the three quality axes."""
    if not row:
        return None, None, None
    if axis == "humaneval":
        v, n, cap = row.get("passed"), row.get("n"), row.get("max_tokens")
        n = n or row.get("limit_requested")
        return (v / n if v is not None and n else None), n, cap
    if axis == "mmlu_pro":
        v, n, cap = row.get("correct"), row.get("n"), row.get("max_tokens")
        n = n or row.get("limit_requested")
        return (v / n if v is not None and n else None), n, cap
    if axis == "ifeval":
        n = row.get("n") or row.get("limit_requested")
        return row.get("prompt_level_strict_acc"), n, row.get("gen_max_toks")
    return None, None, None


def diff_interval(m: dict, a: str, b: str, axis: str, z: float = 1.96) -> tuple[float, float] | None:
    va, na, _ = score(m.get((a, axis)), axis)
    vb, nb, _ = score(m.get((b, axis)), axis)
    if va is None or vb is None or not na or not nb:
        return None
    fa, fb, ia, ib = float(va), float(vb), int(na), int(nb)
    se = math.sqrt(fa * (1 - fa) / ia + fb * (1 - fb) / ib)
    return abs(fb - fa) * 100, z * se * 100


def footprint(model: dict, ctx: int) -> float:
    """matrix.py's expression: weights + q8_0 KV + the sliding-window fixed cost + 1 GiB overhead."""
    kv = model.get("kv_mib_per_ktok", 0) * (ctx / 1024) * 0.5
    swa = model.get("swa_fixed_mib", 0) * 0.5
    draft = model.get("draft_gib", 0) or 0
    return model["size_gib"] + draft + (kv + swa) / 1024 + 1.0


def main() -> int:
    md_path, matrix_path, runs_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    md = open(md_path, encoding="utf-8").read()
    body = md.split("## 16. Document history")[0]          # history entries are exempt
    mx = json.load(open(matrix_path, encoding="utf-8"))
    models = {m["id"]: m for m in mx["models"]}
    rows, allrows = newest_rows(runs_dir)
    CAPNOTE: list[str] = []

    # A cell may quote an arm at the cap the page documents for it while a re-run at another cap is
    # landing. Those pairs are listed here rather than inferred: the gate then still catches a real
    # drift at the documented cap, and prints the newer row it is deliberately not using.
    EXCEPTIONS: dict[tuple[str, str], set] = {
        ("gpt-oss-20b-mxfp4", "humaneval"): {512},
        ("gpt-oss-20b-mxfp4", "mmlu_pro"): {512},
        ("gpt-oss-20b-mxfp4", "ifeval"): {1280},
        ("gpt-oss-20b-mxfp4", "riddles"): {None, 1024},
    }

    def cap_of(row: dict) -> int | None:
        return row.get("max_tokens") or row.get("gen_max_toks") or row.get("riddle_max_toks")

    def pick(mid: str, axis: str) -> dict | None:
        rws = allrows.get((mid, axis)) or []
        if not rws:
            return None
        newest = max(rws, key=lambda r: r.get("ts") or 0)
        allowed = EXCEPTIONS.get((mid, axis))
        if allowed:
            at = [r for r in rws if cap_of(r) in allowed]
            if at:
                chosen = max(at, key=lambda r: r.get("ts") or 0)
                note = f"{mid}/{axis}: quoting cap {cap_of(chosen)}, newer row at cap {cap_of(newest)}"
                if chosen is not newest and note not in CAPNOTE:
                    CAPNOTE.append(note)
                return chosen
        return newest
    target = mx.get("target_pool_gib", 15.0)

    print("check-derived: 16 GiB page against the archive")

    # ---- roster arithmetic ---------------------------------------------------
    files = {m["file"] for m in models.values()}
    dup_rows = len(models) - len(files)
    total = sum(next(m["size_gib"] for m in models.values() if m["file"] == f) for f in files)
    ok("roster row/file counts", f"{len(models)} measured rows over {len(files)} weight files" in md,
       f"{len(models)}/{len(files)}")
    ok("files carrying two rows", dup_rows == 3 and "three files carry two rows each" in md, f"{dup_rows}")
    ok("weights total", f"{total:.1f} GiB" in md, f"{total:.1f} GiB")

    # ---- ladder at 8k --------------------------------------------------------
    for gib, expect in ((7, 2), (11, 4), (target, 17), (23, 20), (31, 21)):
        n = sum(1 for m in models.values() if footprint(m, 8192) <= gib)
        ok(f"ladder at {gib} GiB", n == expect and f"{n} of {len(models)}" in md, f"computed {n} of {len(models)}")

    # ---- the two-row intervals the page quotes ------------------------------
    for name, a, b, axis, expect in (
        ("Table 4 HumanEval", "lfm25-24b-a2b-think", "clover-35b-a3b-iq2", "humaneval", 4.4),
        ("Table 4 MMLU-Pro", "clover-35b-a3b-iq2", "axion-1.0-35b-iq3", "mmlu_pro", 10.1),
        ("Table 6 MMLU-Pro", "g4-12b-qat", "g4-26b-a4b-qat", "mmlu_pro", 12.4),
    ):
        got = diff_interval({(m, ax): pick(m, ax) for m in (a, b) for ax in (axis,)}, a, b, axis)
        if got is None:
            ok(name, False, "missing run rows")
            continue
        margin, half = got
        printed = f"±{Decimal(str(half)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}-point"
        ok(f"{name} interval", abs(half - expect) < 0.15 and printed in md,
           f"computed ±{half:.1f} for a {margin:.1f}-point gap, page prints {printed}")
    ok("no single-score interval used for a two-row claim", "±7.7-point" not in body)

    # ---- counts that drift ---------------------------------------------------
    def thinks(m):
        flag = m.get("reasoning")
        return flag is None or str(flag).lower() != "off"

    reasoning = [m for m in models.values() if thinks(m)]
    perf_only = {mid for mid in models if rows.get((mid, "humaneval")) is None}
    thinking = [m for m in reasoning if m["id"] not in perf_only]
    ok("reasoning-arm count", len(thinking) == 9 and "**nine** rows whose templates open a think block" in md,
       f"{len(thinking)} thinking arms with quality rows, {len(reasoning)} flagged non-off")
    wide = [m for m in thinking if m["id"] != "gpt-oss-20b-mxfp4"]
    ok("4096-cap reasoning arms", len(wide) == 8
       and "eight of the nine reasoning arms" in md and "eight of nine reasoning arms" in md, f"{len(wide)}")

    he8192 = [mid for mid in models if (score(pick(mid, "humaneval"), "humaneval")[2]) == 8192]
    ok("8192-cap HumanEval arms", len(he8192) == 4 and "four 8192-cap arms" in md, f"{len(he8192)}: {sorted(he8192)}")

    r14 = sum(1 for m in models
              if (pick(m, "riddles") or {}).get("score") == (pick(m, "riddles") or {}).get("total") == 14)
    ok("riddle tally at 14/14", r14 == 15 and "fifteen models tied" in md, f"computed {r14}")

    ok("§3 riddle denominator", "15 of the 21 rows" in md,
       "the page states a denominator that is not the roster's row count")
    kv36 = [m["id"] for m in models.values() if m.get("kv_mib_per_ktok") == 36]
    ok("rows at 36 MiB per 1k", len(kv36) == 6 and "Six rows land at 36" in md, f"computed {len(kv36)}: {sorted(kv36)}")

    # ---- Table 2's derived columns ------------------------------------------
    means: dict[str, float] = {}
    for mid in models:
        vals = [score(pick(mid, ax), ax)[0] for ax in ("humaneval", "mmlu_pro", "ifeval")]
        if all(v is not None for v in vals):
            means[mid] = sum(float(v) for v in vals if v is not None) / 3.0
    top = max(means, key=means.get) if means else ""
    ok("mean leader is the low-cap row named in prose", top == "huihui-gemma26b-qat-abl" and "0.881" in md,
       f"computed leader {top} at {means.get(top, 0):.3f}")

    bad_means = []
    for line in md.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 12 or cells[0] not in means:
            continue
        try:
            printed = float(cells[9])
        except ValueError:
            continue
        if abs(printed - means[cells[0]]) > 0.0015:
            bad_means.append(f"{cells[0]} prints {printed:.3f}, archive {means[cells[0]]:.3f}")
    ok("every mean in Table 2 matches the archive", not bad_means, "; ".join(bad_means[:4]))

    # ---- every footprint in Table 2, from the stated arithmetic ------------
    bad_fp = []
    for line in md.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 12 or cells[0] not in models:
            continue
        try:
            printed = float(cells[3].split()[0])
        except (ValueError, IndexError):
            continue
        m = models[cells[0]]
        calc = footprint(m, m["ctx"])
        if abs(printed - calc) > 0.006:      # the page prints 2 dp; 18.275 legitimately reads 18.28
            bad_fp.append(f"{cells[0]} prints {printed:.2f}, arithmetic {calc:.3f}")
    ok("every Table 2 footprint re-derives", not bad_fp, "; ".join(bad_fp[:4]))

    # ---- Table 5 carries the SWA term, so a footprint can be done by hand --
    bad_swa = []
    for line in md.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 7 or cells[0] not in models:
            continue
        swa = models[cells[0]].get("swa_fixed_mib", 0)
        want = f"{swa * 0.5 / 1024:.3f}" if swa else "—"
        if cells[2] != want:
            bad_swa.append(f"{cells[0]} prints {cells[2]}, arithmetic {want}")
    ok("Table 5's SWA column", not bad_swa, "; ".join(bad_swa[:4]))

    # the hand recipe must close: weights + context column + SWA + 1 GiB
    worst = None
    for line in md.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 7 or cells[0] not in models:
            continue
        m = models[cells[0]]
        col = {8192: 3, 16384: 4, 32768: 5, 65536: 6}.get(m["ctx"])
        if not col:
            continue
        try:
            kv = float(cells[col]); swa = 0.0 if cells[2] == "—" else float(cells[2])
        except ValueError:
            continue
        hand = m["size_gib"] + (m.get("draft_gib", 0) or 0) + kv + swa + 1.0
        if worst is None or abs(hand - footprint(m, m["ctx"])) > worst[1]:
            worst = (m["id"], abs(hand - footprint(m, m["ctx"])), hand)
    ok("Table 5 + weights + 1 GiB reproduces Table 2", worst is not None and worst[1] < 0.006,
       f"largest gap {worst[0]} {worst[1]:.3f} GiB" if worst else "no rows matched")

    # ---- §4's HumanEval band is pair-specific -------------------------------
    for a, b, want in (("lfm25-24b-a2b-think", "clover-35b-a3b-iq2", 4.4),
                       ("g4-12b-qat", "g4-26b-a4b-qat", 6.5)):
        got = diff_interval({(x, "humaneval"): pick(x, "humaneval") for x in (a, b)}, a, b, "humaneval")
        half = f"±{got[1]:.1f}" if got else "?"
        ok(f"§4 HumanEval band {a}/{b}", got is not None and abs(got[1] - want) < 0.1 and half in md,
           f"computed {half}, page states {want}")

    # ---- all six two-row bands, to one decimal, Decimal HALF_UP ------------
    pairs = (("lfm25-24b-a2b-think", "clover-35b-a3b-iq2", "humaneval", "4.4"),
             ("g4-12b-qat", "g4-26b-a4b-qat", "humaneval", "6.5"),
             ("clover-35b-a3b-iq2", "axion-1.0-35b-iq3", "mmlu_pro", "10.1"),
             ("g4-12b-qat", "g4-26b-a4b-qat", "mmlu_pro", "12.4"),
             ("lfm25-24b-a2b-htc-think", "lfm25-24b-a2b-think", "ifeval", "10.0"),
             ("lfm25-24b-a2b-think", "g4-26b-a4b-qat", "ifeval", "12.2"))
    for a, b, axis, want in pairs:
        got = diff_interval({(x, axis): pick(x, axis) for x in (a, b)}, a, b, axis)
        if got is None:
            ok(f"band {axis} {a}/{b}", False, "missing rows")
            continue
        printed = str(Decimal(str(got[1])).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
        ok(f"band {axis} {a}/{b}", printed == want and f"±{printed}" in md,
           f"computed ±{printed}, page says ±{want}")

    # ---- §8 names all sixteen other quality rows --------------------------
    seg = md[md.find("Of the other sixteen quality rows"): md.find("Of the other sixteen quality rows") + 1400]
    named = [mid for mid in means if mid in seg]
    ok("§8 names all sixteen", len(named) == len(means) - 3 and "sixteen" in seg,
       f"{len(named)} named, {len(means) - 3} expected")

    # ---- Figure 6's threshold counts ---------------------------------------
    vals = sorted(means.values(), reverse=True)
    for thr, want in ((0.78, 10), (0.85, 3), (0.75, 13)):
        got = sum(1 for v in vals if v > thr)
        word = {3: "three", 10: "ten", 13: "thirteen"}[want]
        ok(f"Figure 6 threshold {thr}", got == want and f"{word} " in md, f"{got} rows above {thr}")

    # ---- the load-time arithmetic ------------------------------------------
    biggest = max(m["size_gib"] for m in models.values())
    gb = biggest * 1.073741824
    ok("storage load-time figure",
       f"about {gb / 1.9:.0f} s" in md and f"up to {gb / 0.5:.0f} s" in md,
       f"{biggest} GiB = {gb:.2f} GB -> {gb/1.9:.0f} s at 1.9 GB/s, {gb/0.5:.0f} s at 0.5")

    # ---- §10: the drafter's cost at a matched context ---------------------
    base8 = footprint(models["g4-26b-a4b-qat"], 8192)
    mtp8 = footprint(models["g4-26b-a4b-qat-mtp"], 8192)
    ok("§10 drafter arithmetic at 8k",
       f"{base8:.2f}" in md and f"{mtp8:.2f}" in md and abs((mtp8 - base8) - 0.43) < 0.005
       and "at the same 8k context" in md,
       f"8k: {base8:.2f} vs {mtp8:.2f}, delta {mtp8 - base8:.3f}")

    # ---- the footnote's rounding examples, from the counts ------------------
    for mid in ("lfm25-24b-a2b-think", "mistral-24b-q4"):
        vals = [score(pick(mid, ax), ax)[0] for ax in ("humaneval", "mmlu_pro", "ifeval")]
        if any(v is None for v in vals):
            ok(f"footnote example {mid}", False, "missing run rows")
            continue
        mean4 = sum(float(v) for v in vals if v is not None) / 3.0
        ok(f"footnote example {mid}", f"{mean4:.4f}" in md and f"{mean4:.3f}" in md,
           f"computed {mean4:.4f} (prints {mean4:.3f})")

    # ---- what the provenance manifest actually covers ----------------------
    prov_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "data", "provenance.json")
    if os.path.exists(prov_path):
        prov = json.load(open(prov_path, encoding="utf-8"))
        covered = {f["file"].split("/")[-1] for v in prov.values() for f in v.get("files", [])}
        roster = {m["file"] for m in models.values()}
        inside = sorted(roster & covered)
        words = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 16: "sixteen"}
        spelled = words.get(len(inside), str(len(inside)))
        ok("§14 provenance coverage",
           (f"only {len(inside)} of this page's {len(roster)} roster files are in it" in md
            or f"only {spelled} of this page's {len(roster)} roster files" in md)
           and all(f in md for f in inside),
           f"computed {len(inside)} of {len(roster)}: {inside}")

    # ---- Table 10 and the card count ----------------------------------------
    cards = re.search(r"\| card \| memory \| peak bandwidth.*?\n((?:\|.*\n)+)", md)
    n_cards = len([l for l in cards.group(1).splitlines()
                   if l.startswith("|") and not l.strip().startswith("|---")]) if cards else 0
    ok("card table has the reference plus twelve vendor rows", n_cards == 13, f"{n_cards} rows")

    # ---- figures fit percentages and §12's ratio ranges ---------------------
    e4b = footprint(models["g4-e4b-qat"], models["g4-e4b-qat"]["ctx"])
    clover = footprint(models["clover-35b-a3b-iq2"], models["clover-35b-a3b-iq2"]["ctx"])
    pct = 100 * e4b / clover
    ok("§8 budget pick as a share of the mean pick",
       f"{pct:.0f}% of the mean pick's {clover:.2f} GiB footprint" in md,
       f"computed {pct:.1f}% of {clover:.2f} GiB ({e4b:.2f} GiB)")

    moe_gb = 4.0 * 4.58 / 8.0          # the 26B-A4B: 4B active at the file's effective bpw
    dense_gb = 11.907 * 4.52 / 8.0     # the 12B dense
    ref_moe, ref_dense = 59.0, 28.0    # measured on this host (Table 10, reference row)

    def half_up(x: float) -> str:
        return str(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    def bands(bws, lo_hi=(0.35, 0.55)):
        lo, hi = min(bws), max(bws)
        moe = [(lo / moe_gb) * lo_hi[0] / ref_moe, (hi / moe_gb) * lo_hi[1] / ref_moe]
        dn = [(lo / dense_gb) * 0.55 / ref_dense, (hi / dense_gb) * 0.78 / ref_dense]
        return moe, dn

    small = bands([288, 320, 448])
    mid = bands([512, 560, 576, 624, 640, 672])
    for label, (moe, dn) in (("128-bit group", small), ("256-bit group", mid)):
        want = (f"{half_up(moe[0])}–{half_up(moe[1])}×", f"{half_up(dn[0])}–{half_up(dn[1])}×")
        ok(f"§12 {label} ratio ranges",
           want[0] in md and want[1] in md, f"computed MoE {want[0]}, dense {want[1]}")

    # ---- §6 must name the rows Table 5 actually lists at 36 MiB -------------
    at36 = sorted(mid_ for mid_, m in models.items() if m.get("kv_mib_per_ktok") == 36)
    seg = md[md.find("Six rows land at 36"): md.find("Six rows land at 36") + 700]
    missing = [m for m in at36 if m not in seg]
    ok("§6 names the six 36-MiB rows", not missing and "`-htc` rows" not in seg,
       f"missing {missing}" if missing else "the -htc pair is wrongly included")

    # ---- lint: joined words and lost spaces ---------------------------------
    # Code spans, link targets and bare identifiers carry dots and colons legitimately,
    # so they are stripped before the punctuation rule runs.
    # Backticks are removed but their content is kept: the failure this catches is punctuation
    # butting against a code span ("ceiling.`qwen3-30b`"), which deleting the span would hide.
    prose = body.replace("`", "")
    prose = re.sub(r"\]\([^)]*\)", " ", prose)
    prose = re.sub(r"https?://\S+", " ", prose)
    prose = re.sub(r"^\|.*$", " ", prose, flags=re.M)          # table rows: ids and figures
    # identifiers carry legitimately joined letters: filenames, domains, versions, e.g./i.e.
    for pat in (r"\b[\w-]+\.(py|sh|html|md|cpp|json|gguf|cff|txt|svg|log|out|jsonl|yml|toml)\b",
                r"\b[\w-]+\.(com|org|io|net|dev)\b", r"\b\d+\.\d+\b", r"\b[ei]\.[gse]\."):
        prose = re.sub(pat, " ", prose, flags=re.I)
    lint = []
    for i, line in enumerate(prose.splitlines(), 1):
        for m in re.finditer(r"[a-z][.:][A-Za-z]", line):
            lint.append(f"line {i}: {line[max(0, m.start() - 30):m.end() + 20]!r}")
        for m in re.finditer(r"(?<![a-z])(and|the|of|to|in|is)(the|and|of|to|in)(?![a-z])", line):
            if m.group(0) in ("into", "onto", "unto"):
                continue
            lint.append(f"line {i}: joined function words {m.group(0)!r}")
        for bad in ("rowswhose", "andthe", "ofit", "tothe", "inthe", "atthe"):
            if bad in line:
                lint.append(f"line {i}: joined word {bad!r}")

    # the rendered page: attribute values and figcaptions, where the md cannot show the result
    if len(sys.argv) > 4 and os.path.exists(sys.argv[4]):
        page = open(sys.argv[4], encoding="utf-8").read()
        # figures are checked at source, and the JSON-LD block is machine data, not prose
        page = re.sub(r"<svg.*?</svg>", " ", page, flags=re.S)
        page = re.sub(r"<script.*?</script>", " ", page, flags=re.S)
        page = re.sub(r"<style.*?</style>", " ", page, flags=re.S)
        page = re.sub(r"<pre.*?</pre>", " ", page, flags=re.S)
        # the document-history table quotes the old, broken strings on purpose; it is a record, not prose
        m = re.search(r"<h2[^>]*>\s*16\.\s*Document history", page)
        if m:
            end = page.find("</table>", m.start())
            if end > 0:
                page = page[:m.start()] + " " + page[end + len("</table>"):]

        def clean(txt: str) -> str:
            for pat in (r"https?://\S+", r"(?:/[\w.\-]+)+",
                        r"\b[\w-]+\.(py|sh|html|md|cpp|json|gguf|cff|txt|svg|log|out|jsonl|yml|toml)\b",
                        r"\b[\w-]+\.(com|org|io|net|dev)\b", r"\b\w+\.\w+_\w+\b",
                        r"\b\d+\.\d+\b", r"\b[ei]\.[gse]\."):
                txt = re.sub(pat, " ", txt, flags=re.I)
            return txt
        for attr in ("alt", "aria-label", "title"):
            for m in re.finditer(attr + r'="([^"]*)"', page):
                val = clean(m.group(1))
                for j in re.finditer(r"[a-z][.:,][A-Za-z]", val):
                    lint.append(f"{attr}: {val[max(0, j.start() - 25):j.end() + 15]!r}")
        # inline tags disappear (so punctuation butting against a code span shows), block tags become
        # a boundary (so two adjacent table cells are not glued into one word)
        inline = re.sub(r"</?(code|b|i|em|strong|a|span|abbr)(\s[^>]*)?>", "", page)
        text = clean(re.sub(r"<[^>]+>", " ", inline))
        for j in re.finditer(r"[a-z][.:,][A-Za-z]", text):
            snippet = text[max(0, j.start() - 30):j.end() + 20]
            lint.append(f"rendered text: {snippet!r}")
    ok("no joined words or lost spaces", not lint, "; ".join(lint[:6]))

    # ---- phrases that were true two revisions ago ---------------------------
    for stale in ("a third of the dense rate", "eleven models tied", "for fourth",
                  "the whole roster fits at 24 GB", "the three 8192-cap arms",
                  "for the four reasoning arms", "the five arms whose templates",
                  "thirteen 16 GB cards", "outside the ±7.7-point interval"):
        ok(f"stale phrase gone: {stale!r}", stale not in body)

    if CAPNOTE:
        print(f"       note: {len(CAPNOTE)} cell(s) quoted at the documented cap with a newer row at another:")
        for line in CAPNOTE:
            print(f"             {line}")
    print(f"check-derived: {PASSES} checks passed, {len(FAILS)} failed")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
