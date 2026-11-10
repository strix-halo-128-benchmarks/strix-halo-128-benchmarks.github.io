# Local LLM benchmarks on AMD Strix Halo (gfx1151)

Measured capability **and** throughput for local models on a single **Minisforum MS-S1 MAX**
(Ryzen AI Max+ 395, Radeon 8060S, 128 GB unified memory, ~100 GiB GTT, ~600 GiB of models on a 4 TB
NVMe, zram swap), on llama.cpp/Vulkan.

**Read the report: https://strix-halo-128-benchmarks.github.io/**

- **[Leaderboards by axis](https://strix-halo-128-benchmarks.github.io/leaderboards.html)** — code,
  knowledge, reasoning, decode, prefill, one axis per table with cap and build on every row.
- **[Retired models](https://strix-halo-128-benchmarks.github.io/retired.html)** — what was deleted, why,
  with file sizes, sha256s and restore recipes.
- **[Change log](https://strix-halo-128-benchmarks.github.io/changelog.html)** — every correction and the
  measurement that forced it.
- **[16 GiB of VRAM](https://strix-halo-128-benchmarks.github.io/16gb.html)** — a second, separate question:
  which models fit a 16 GiB graphics card, what they score there, what the KV cache costs at each context,
  and how the answer changes between a unified APU, a discrete card and Apple Silicon.

Two documents:

| Page | What it is |
|---|---|
| [index.html](index.html) | the report — method, measured matrix, league tables, figures, per-model analysis |
| [16gb.html](16gb.html) | the 16 GiB card page — a roster defined by what fits 16 GiB of VRAM, measured
  on the same host, with fit arithmetic, KV/context budgets, a quantisation ladder and a three-platform
  comparison |
| [retired-models.html](retired-models.html) | the retirement ledger — every deleted model with the reason, the measured scores that justified it, file sizes, sha256s, upstream repo and the flags that worked, so any deletion can be reversed or re-tested |

Every number in the report comes from a run recorded in [`data/catalogue.json`](data/catalogue.json):
154 rows across 75 model aliases, 2026-10-07 → 2026-11-06. Retired models keep their rows there too,
marked with the retirement date.

## Why this exists

Public numbers for this platform are almost entirely tokens-per-second. That answers "how fast",
not "is it good", and it can't answer "is this file worth 47 GiB of download". This report adds the
capability axis — HumanEval pass@1 and MMLU-Pro accuracy, each recorded **with the max_tokens cap it
was measured at** — joined to a specific quant and weight file, plus the retirements and the reasons.

## Headline findings

- **The plateau.** The top five models span 2.2 pp of HumanEval while spanning 15.6 GiB to 63 GiB of
  weights. Above roughly 0.95 code / 0.85 knowledge, this box buys nothing with more parameters.
- **The cap trap.** A row measured at `max_tokens` 512 is a floor, not a measurement. Re-measuring one
  35B file at 4096 moved one item (0.5610 → 0.5671); re-measuring another moved fourteen. Only a re-run
  tells you which.
- **Quantisation attacks axes selectively.** One 2-bit MoE kept 0.945 HumanEval while collapsing to
  0.3667 MMLU — procedural skill survived, factual knowledge did not.
- **"Arch is implemented" is necessary, not sufficient.** A 119B MoE loaded and served correctly at
  4.8 tok/s because its architecture inherits another family's decode path. Benchmark the file, not the
  architecture registry.

## Method, briefly

1. Each candidate runs beside the resident driver on a transient systemd unit, so the machine's real
   workloads never stop and the model is measured under the memory pressure it would actually see.
2. Capability axes are HumanEval (164 items, tests executed) and MMLU-Pro (120 items, chat 0-shot),
   each at a stated cap. Prefill (pp) and decode (tg) come from the same server.
3. Build identity — llama.cpp commit, kernel, mesa — is recorded per run, because a kernel bump moves
   decode 10–20% and silently invalidates comparisons.
4. Rows are only compared at matched caps. Anything measured at 512 is flagged as a floor.
5. Deleted models keep their rows, marked with the retirement date, and their recipes are kept so a
   claim can be re-tested.

## What it is not

Not a benchmark of these models in general — it is one machine, one software stack, stated caps.
Not a leaderboard: sample sizes are 164 and 120, so ±3–4 pp is noise, and the report says so wherever
it compares close scores. Not affiliated with AMD, llama.cpp, or any model vendor.

## Related sources

| Question | Where |
|---|---|
| throughput on this GPU, many setups | [llamaperf.com/gpu/strix-halo-128gb](https://llamaperf.com/gpu/strix-halo-128gb) |
| backend choice, pp/tg sweeps | [lhl/strix-halo-testing](https://github.com/lhl/strix-halo-testing/tree/main/llm-bench), [kyuz0 toolboxes](https://kyuz0.github.io/amd-strix-halo-toolboxes/) |
| platform guides, setup | [strixhalo.wiki](https://strixhalo.wiki/) |
| llama.cpp backend bugs and datapoints | [gfx1151 discussions](https://github.com/ggml-org/llama.cpp/discussions/20856) |

## Cost

154 measured runs, **58.6 hours of benchmark execution** — that figure is exact, from the archive.
Building the report around them was an estimated 220–320 hours, of which 40–60 needed a person;
reproducing the numbers elsewhere is roughly 40–60 hours now that the harness and tools are public
(§18.4 of the report). Decode rates will not transfer between builds even when the quality rows do.

## Credits

Measurements, analysis and the writing of these documents were done with **Hermes Agent**
(Nous Research) driven by **DeepSeek `deepseek-flash`**, working alongside the machine's operator over
four weeks. The model scheduled and monitored the benchmark runs, read their outputs and drafted the
text; the hardware produced the measurements, and every figure is traceable to a run id in the
catalogue.

## Licence and citation

Text, figures and data: **CC BY 4.0**. See [LICENSE](LICENSE). Reuse the numbers freely with
attribution; if you disagree with one, the run ids and caps are in the data so you can check it.

```
Local LLM benchmarks on AMD Strix Halo (gfx1151), measured 2026-10-07 → 2026-10-31.
https://strix-halo-128-benchmarks.github.io/
```
