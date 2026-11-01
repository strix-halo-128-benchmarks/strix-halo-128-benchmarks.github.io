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
banner = ("\n> **Also published:** [Retired models — what was deleted, why, with hashes and "
          "restore recipes](retired-models.html).\n")
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

echo "== 4. figures into the repo"
cp "$DOCS"/charts/*.svg "$REPO/charts/"

echo "== 5. render both pages"
"$PY" "$DOCS/md2html.py" "$REPO/strix-halo-llm-testing.md" "$REPO/index.html" \
      "Local LLM benchmarks on AMD Strix Halo (gfx1151)"
"$PY" "$DOCS/md2html.py" "$REPO/retired-models.md" "$REPO/retired.html" \
      "Retired local models — restore recipes"

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
for f in "$REPO"/*.md "$REPO"/*.html; do leakcheck "$f"; done
echo "   ok: report $(stat -c%s "$REPO/index.html") B / $(grep -c '<svg' "$REPO/index.html") figures," \
     "ledger $(stat -c%s "$REPO/retired.html") B, cross-linked"
echo "== done — review 'git diff', then commit"
