# Tools behind the measurements

Two probes that produced figures in the report, published so the claims can be re-run rather than
believed. Both talk to a llama.cpp server over its OpenAI-compatible API — no model is loaded, no
unit is touched, so they are safe to run against a server that is doing real work.

    benchlib.py   the HTTP/timing shim (chat completion → content, token counts, prefill/decode rates)
    checks.py     the harness's checks, including the needle-in-a-haystack probe
    ctxcurve.py   context-scaling curve (§23.2 of the report)
    lucebox30.py  an independent 30-item quality suite (§23.3), fetched from Luce-Org/lucebox

## Context curve

    python3 ctxcurve.py --port 8100 --sizes 2000,8000,32000,65536,128000 --tag mybox

Records, per depth: the prompt length the server actually saw, whether the planted passphrase was
retrieved, wall time, and llama.cpp's own prefill and decode rates. Rows append to `~/runs/<tag>.jsonl`.

What it found here: retrieval held at every depth to 112,862 prompt tokens, while prefill fell 2.6×
(1,715 → 670 t/s) and decode 1.5× (57.2 → 37.7 t/s). The decode curve is the one that matters for
chat, and its steepest step is between 58k and 113k — so compact before 64k, not at the window edge.

## Cross-validation suite

    python3 lucebox30.py --port 8100 --suites he,gsm,math --tag mybox

Pulls the fixtures pinned at `Luce-Org/lucebox@90f85fa`, runs 30 items at their own per-item caps
(512 / 1024 / 2048) and temperature 0, executes coding answers against the fixture's `gold_test`,
and scores GSM8K and math numerically.

**Two warnings, both learned the hard way.** First, the fixture's `gold_answer` for `math_08` is 20
where the correct value is 20/3 — the source's own results.json records that correction, and
`GOLD_CORRECTIONS` applies it. Second, and more important: **a naive grader disagrees with this suite
by 4 items out of 30.** Taking the last number in a sentence scores "$64 for the 16 glasses" as 16;
comparing LaTeX to plain notation marks −2/3 wrong against `-\frac{2}{3}`; a `\\boxed{…}` regex without
brace matching truncates `\frac{20}{3}`. All four are fixed here, and every row records the numbers
found in the answer sentence plus the raw final text, so a verdict can be audited without re-running.

If you publish quality numbers from any suite, publish the grader with them. On 30 items, a grader
defect is worth 3.3 pp, and an unpublished one is an unknown error bar.
