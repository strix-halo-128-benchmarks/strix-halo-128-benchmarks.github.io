#!/usr/bin/env bash
# Regenerate the published site from the measurement pipeline. Idempotent: run it after any new
# benchmark, then commit. Nothing here edits the source documents — it sanitises copies of them.
set -euo pipefail

DOCS="${DOCS:-$HOME/docs}"
RUNS="${RUNS:-$HOME/runs}"
LOCAL="${LOCAL:-$HOME/llama-local}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PY="$DOCS/.venv/bin/python"
SKILL="$HOME/.hermes/skills/software-development/local-model-benchmark-suite"
LEAKS='mss1-max|192\.168\.|100\.115\.|/home/|@g\.us'

leakcheck() {  # $1 = file to test
  if grep -qEI "$LEAKS" "$1"; then
    echo "REFUSING TO PUBLISH: identifier found in $1"
    grep -nEI "$LEAKS" "$1" | head -5
    exit 1
  fi
}

echo "== 1. catalogue from the run archive"
"$PY" "$SKILL/scripts/runs-catalogue.py"

echo "== 2. figures from the catalogue (needs matplotlib, hence $PY)"
(cd "$DOCS" && "$PY" charts.py)
echo "== 2b. figures for the 16 GiB page (same archive, same conventions)"
(cd "$DOCS" && "$PY" charts16.py)

echo "== 3. sanitised report"
mkdir -p "$REPO/charts" "$REPO/data"
python3 - "$DOCS/strix-halo-llm-testing.md" "$REPO/strix-halo-llm-testing.md" <<'PY'
import sys
src, dst = sys.argv[1], sys.argv[2]
txt = open(src, encoding="utf-8").read()
# Privacy pass: the internal document names the host and its monitor; the public copy must not.
for a, b in (("`mss1-max`", "the reference host"),
             ("`mss1-max-hwinfo`", "the hardware monitor"),
             ("mss1-max-hwinfo", "the hardware monitor"),
             ("(hardware monitor, tailnet-only)", "(hardware monitor, private network only)")):
    txt = txt.replace(a, b)
banner = ("\n> **Also published:** [Leaderboards by axis](leaderboards.html) — code, knowledge, "
          "reasoning, decode and prefill, each row with its cap and build · [Retired models — what was "
          "deleted, why, with hashes and restore recipes](retired-models.html) · [Change log](changelog.html) "
          "— every correction and the numbers that forced it · [16 GiB of VRAM — local LLMs](16gb.html) — what "
          "fits on a 16 GiB card, what it scores, and why the answer changes with the memory architecture.\n")
if "retired-models.html" not in txt:
    i = txt.find("\n", txt.find("# "))
    txt = txt[:i] + banner + txt[i:]
footer = ("\n---\n\n*Source, data and build scripts: "
          "[github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io]"
          "(https://github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io). "
          "Every row above is backed by a run id in "
          "[`data/catalogue.json`](data/catalogue.json); corrections are welcome as issues there.*\n")
if "Source, data and build scripts" not in txt:
    txt = txt.rstrip("\n") + "\n" + footer
open(dst, "w", encoding="utf-8").write(txt)
print(f"   {len(txt)} bytes")
PY
leakcheck "$REPO/strix-halo-llm-testing.md"

echo "== 3b. retirement ledger"
python3 - "$LOCAL/RETIRED-models.md" "$REPO/retired-models.md" <<'PY'
import sys
src, dst = sys.argv[1], sys.argv[2]
txt = open(src, encoding="utf-8").read()
nav = ("\n> Part of [Local LLM benchmarks on AMD Strix Halo](index.html). Every deletion here is "
       "reversible: each entry carries file sizes, sha256s, the upstream repo and the flags that "
       "worked.\n")
if "index.html" not in txt:
    i = txt.find("\n", txt.find("# "))
    txt = txt[:i] + nav + txt[i:]
footer = ("\n---\n\n*Source: [github.com/strix-halo-128-benchmarks/"
          "strix-halo-128-benchmarks.github.io](https://github.com/strix-halo-128-benchmarks/"
          "strix-halo-128-benchmarks.github.io). Entries written after 2026-10-30 record the "
          "sha256 before deleting; earlier ones say when a hash was never captured.*\n")
if "Source: [github.com/strix-halo-128-benchmarks" not in txt:
    txt = txt.rstrip("\n") + "\n" + footer
open(dst, "w", encoding="utf-8").write(txt)
print(f"   {len(txt)} bytes")
PY
leakcheck "$REPO/retired-models.md"

echo "== 3b2. change log page (its own document, so the report stays about the measurement)"
python3 - "$DOCS/strix-halo-changelog.md" "$REPO/changelog.md" <<'PY'
import sys
src, dst = sys.argv[1], sys.argv[2]
txt = open(src, encoding="utf-8").read()
for a, b in (("`mss1-max`", "the reference host"), ("mss1-max-hwinfo", "the hardware monitor")):
    txt = txt.replace(a, b)
footer = ("\n---\n\n*Source, data and build scripts: "
          "[github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io]"
          "(https://github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io).*\n")
if "Source, data and build scripts" not in txt:
    txt = txt.rstrip("\n") + "\n" + footer
open(dst, "w", encoding="utf-8").write(txt)
print(f"   {len(txt)} bytes")
PY
leakcheck "$REPO/changelog.md"

echo "== 3c. leaderboards by axis (from the published matrix, so the two cannot disagree)"
python3 "$REPO/scripts/leaderboards.py" "$REPO/strix-halo-llm-testing.md" "$REPO/leaderboards.md"
leakcheck "$REPO/leaderboards.md"

echo "== 3d. 16 GiB VRAM page (its own document: the class is defined by the card, not by this box)"
python3 - "$DOCS/16gb-vram.md" "$REPO/16gb-vram.md" <<'PY'
import sys
src, dst = sys.argv[1], sys.argv[2]
txt = open(src, encoding="utf-8").read()
for a, b in (("`mss1-max`", "the reference host"), ("`mss1-max-hwinfo`", "the hardware monitor"),
             ("mss1-max-hwinfo", "the hardware monitor"), ("mss1-max", "the reference host"),
             ("/home/dom", "~")):
    txt = txt.replace(a, b)
banner = ("\n> **Also published:** [the main report](index.html) — the wider model matrix on this "
          "platform · [leaderboards by axis](leaderboards.html) · [retired models](retired.html) · "
          "[change log](changelog.html).\n")
if "leaderboards.html" not in txt.split("## 1.")[0]:
    i = txt.find("\n", txt.find("# "))
    txt = txt[:i] + banner + txt[i:]
footer = ("\n---\n\n*Source, data and build scripts: "
          "[github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io]"
          "(https://github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io). "
          "Text, figures and data: CC BY 4.0.*\n")
if "Source, data and build scripts" not in txt:
    txt = txt.rstrip("\n") + "\n" + footer
open(dst, "w", encoding="utf-8").write(txt)
print(f"   {len(txt)} bytes")
PY
leakcheck "$REPO/16gb-vram.md"

echo "== 4. figures into the repo"
cp "$DOCS"/charts/*.svg "$REPO/charts/"

echo "== 5. render both pages"
PUBLIC_URL="${PUBLIC_URL:-https://strix-halo-128-benchmarks.github.io}"
export PUBLIC_URL
DESC="Measured capability and throughput for local LLMs on AMD Strix Halo (gfx1151): HumanEval and MMLU-Pro at stated token caps, prefill/decode, quant and build identity per run, 2026-10-07 to 2026-10-31."
"$PY" "$DOCS/md2html.py" "$REPO/strix-halo-llm-testing.md" "$REPO/index.html" \
      "Local LLM benchmarks on AMD Strix Halo (gfx1151)" "$DESC"
"$PY" "$DOCS/md2html.py" "$REPO/retired-models.md" "$REPO/retired.html" \
      "Retired local models — restore recipes" \
      "Every local model retired from the Strix Halo benchmark box: why it went, the scores that justified it, file sizes, sha256s and the flags to restore it."
"$PY" "$DOCS/md2html.py" "$REPO/changelog.md" "$REPO/changelog.html" \
      "Change log — local LLM benchmarks on AMD Strix Halo" \
      "Every version of the Strix Halo LLM report: what changed, and the measurement that forced the change."
"$PY" "$DOCS/md2html.py" "$REPO/leaderboards.md" "$REPO/leaderboards.html" \
      "Leaderboards by axis — local LLMs on AMD Strix Halo" \
      "Per-axis rankings of local LLMs measured on Strix Halo: HumanEval, MMLU-Pro, reasoning traps, decode and prefill, each row with its token cap, item count and llama.cpp build."
"$PY" "$DOCS/md2html.py" "$REPO/16gb-vram.md" "$REPO/16gb.html" \
      "16 GiB of VRAM: which local LLMs fit, and what they score" \
      "Which local LLMs fit a 16 GiB graphics card and what they score: HumanEval, MMLU-Pro and IFEval at stated caps, fit and KV-cache arithmetic, context budgets, dense versus MoE, a decision map, thirteen 16 GB cards compared, and the licence on the data."

echo "== 5b. discovery files (robots + sitemap)"
cat > "$REPO/robots.txt" <<ROBOTS
User-agent: *
Allow: /

Sitemap: ${PUBLIC_URL}/sitemap.xml
ROBOTS
printf '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' > "$REPO/sitemap.xml"
for page in "" "leaderboards.html" "retired.html" "changelog.html" "16gb.html"; do
  printf '  <url><loc>%s/%s</loc><lastmod>%s</lastmod></url>\n' "$PUBLIC_URL" "$page" "$(date +%F)" >> "$REPO/sitemap.xml"
done
printf '</urlset>\n' >> "$REPO/sitemap.xml"
echo "   robots.txt + sitemap.xml written"

echo "== 5c. provenance manifest (repo + licence + verified hashes per artefact)"
cp "$LOCAL/provenance.json" "$REPO/data/provenance.json"
python3 - "$REPO/data/provenance.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
v = sum(1 for x in d.values() if x.get("verified"))
print(f"   {len(d)} artefacts, {v} verified against upstream LFS ids")
PY
leakcheck "$REPO/data/provenance.json"

echo "== 6. sanitised data export"
python3 - "$RUNS/catalogue.json" "$REPO/data/catalogue.json" <<'PY'
import json, sys
rows = json.load(open(sys.argv[1]))
out = []
for r in rows:
    r = dict(r)
    for k in ("build_path", "boot_id"):   # absolute paths and per-boot ids stay private
        r.pop(k, None)
    out.append(r)
json.dump(out, open(sys.argv[2], "w"), indent=1)
print(f"   {len(out)} rows")
PY

echo "== 7. gate"
grep -q '{{svg' "$REPO/index.html" && { echo "FAIL: unresolved figure placeholder"; exit 1; } || true
test "$(grep -c '<svg' "$REPO/index.html")" -ge 10 || { echo "FAIL: expected 10 inline figures"; exit 1; }
grep -q 'retired-models.html' "$REPO/index.html" || { echo "FAIL: report does not link the ledger"; exit 1; }
grep -q 'index.html'          "$REPO/retired.html" || { echo "FAIL: ledger does not link the report"; exit 1; }
grep -q 'leaderboards.html'   "$REPO/index.html"    || { echo "FAIL: report does not link the leaderboards"; exit 1; }
grep -q 'changelog.html'      "$REPO/index.html"    || { echo "FAIL: report does not link the change log"; exit 1; }
grep -q 'index.html'          "$REPO/changelog.html" || { echo "FAIL: change log does not link the report"; exit 1; }
grep -q '16gb.html'        "$REPO/index.html"    || { echo "FAIL: report does not link the 16 GiB page"; exit 1; }
grep -q 'index.html'       "$REPO/16gb.html"     || { echo "FAIL: 16 GiB page does not link the report"; exit 1; }
test "$(grep -c '<svg' "$REPO/16gb.html")" -ge 6 || { echo "FAIL: 16 GiB page should inline 6 figures"; exit 1; }
! grep -q 'missing figure' "$REPO/16gb.html"     || { echo "FAIL: 16 GiB page has an unresolved figure"; exit 1; }
python3 "$REPO/scripts/check-prose.py" "$REPO/strix-halo-llm-testing.md" "$REPO/changelog.md" "$RUNS" \
    || { echo "FAIL: a prose score disagrees with the matrix"; exit 1; }
grep -q 'index.html'          "$REPO/leaderboards.html" || { echo "FAIL: leaderboards do not link the report"; exit 1; }
grep -q 'retired-models.html' "$REPO/leaderboards.html" || { echo "FAIL: leaderboards do not link the ledger"; exit 1; }
test "$(grep -c '<table' "$REPO/leaderboards.html")" -ge 6 || { echo "FAIL: expected 6 leaderboard tables"; exit 1; }
for f in "$REPO"/*.md "$REPO"/*.html "$REPO"/tools/*.py "$REPO"/tools/*.md; do leakcheck "$f"; done
# The report now carries its own version line, so it can be quoted without the change log. Keep the two
# from drifting: the header version must be the newest changelog entry, and both pages must state one.
VER_REPORT=$(grep -oE '^\s*-\s*\*\*Document version:\*\* \*\*[0-9]+\.[0-9]+\*\*' "$REPO/strix-halo-llm-testing.md" | grep -oE '[0-9]+\.[0-9]+' | head -1 || true)
VER_CHANGELOG=$(grep -oE '^### Version [0-9]+\.[0-9]+' "$DOCS/strix-halo-changelog.md" | head -1 | grep -oE '[0-9]+\.[0-9]+' || true)
[ -n "$VER_REPORT" ] || { echo "FAIL: report header has no 'Document version' line"; exit 1; }
[ "$VER_REPORT" = "$VER_CHANGELOG" ] || { echo "FAIL: report says v$VER_REPORT, newest changelog entry is v$VER_CHANGELOG"; exit 1; }
VER_16=$(grep -oE '^\s*-\s*\*\*Document version:\*\* \*\*[0-9]+\.[0-9]+\*\*' "$REPO/16gb-vram.md" | grep -oE '[0-9]+\.[0-9]+' | head -1 || true)
[ -n "$VER_16" ] || { echo "FAIL: 16 GiB page has no 'Document version' line"; exit 1; }
echo "   ok: versions — report v$VER_REPORT (== newest changelog entry), 16 GiB page v$VER_16"
echo "   ok: report $(stat -c%s "$REPO/index.html") B / $(grep -c '<svg' "$REPO/index.html") figures," \
     "ledger $(stat -c%s "$REPO/retired.html") B, cross-linked"
echo "== done — review 'git diff', then commit"
