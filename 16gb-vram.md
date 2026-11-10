# 16 GiB of VRAM: which local models actually fit, and what they score

- **Document version:** **1.0** · published 2026-11-10 · first release of this page
- **Measured:** 2026-11-10 · 11 weight files, 113.8 GiB · one llama.cpp build, one KV setting, one slot
- **Axes:** HumanEval 164 items · MMLU-Pro 120 · IFEval 50 prompts · needle 2k/8k · riddles 14 · protocol 3
- **History of this page:** §13 · **Wider report on this platform:** [index.html](index.html)



A 16 GiB graphics card is the tightest interesting class of consumer accelerator: 16 GiB of VRAM, about 15 GiB usable once the driver and runtime have taken their share, and a hard wall at the end of it. This page answers two questions about that class. Which open-weight models fit, and what do they score. Then: how much of that answer depends on the memory architecture underneath, because the same 13.4 GiB file behaves very differently on a unified-memory APU, a discrete card and an Apple SoC.

Every number here was measured on a machine that does **not** have the constraint being studied. The reference host has 100 GiB of GPU-addressable memory, so no model is truncated or spilled while it is being benchmarked. That is deliberate: the scores describe the model, the arithmetic describes the card, and the two are never confounded. Where a figure is arithmetic rather than measurement, it says so.

Eleven files, 164-item HumanEval, 120-item MMLU-Pro, 50-prompt IFEval, 113.8 GiB of weights, one build.

> **Also published:** [the main report](index.html) — the wider model matrix on this platform · [leaderboards by axis](leaderboards.html) · [retired models](retired.html) · [change log](changelog.html).

## 1. The roster

| model | class | weights GiB (bpw) | footprint at its context | context | pp / tg t/s | HumanEval | MMLU-Pro | IFEval | riddles |
|---|---|---|---|---|---|---|---|---|---|
| g4-e4b-qat | dense | 3.93 (4.52) | 5.40 ok | 32k | 2243 / 58 | 0.866 | 0.467 | 0.900 | 14/14 |
| qwen3-8b-q4 | dense | 4.68 (4.91) | 7.93 ok | 32k | 1300 / 39 | 0.787 | 0.583 | 0.900 | 13/14 |
| g4-12b-qat | dense | 6.26 (4.52) | 7.67 ok | 32k | 911 / 28 | 0.896 | 0.575 | 0.920 | 14/14 |
| qwen3-14b-q4 | dense | 8.38 (4.87) | 10.63 ok | 16k | 743 / 24 | 0.854 | 0.608 | 0.880 | 14/14 |
| gpt-oss-20b-mxfp4 | MoE | 11.28 (4.63) | 12.65 ok | 32k | 2169 / 74 | 0.585 | 0.558 | 0.480 | 14/14 |
| lfm25-24b-a2b | MoE | 12.65 (4.53) | 13.96 ok | 32k | 3345 / 110 | 0.640 | 0.192 | 0.860 | 13/14 |
| lfm25-24b-a2b-think | MoE | 12.65 (4.53) | 13.96 ok | 32k | 3360 / 111 | 0.970 | 0.692 | 0.920 | 14/14 |
| mistral-24b-q4 | dense | 13.35 (4.86) | 14.66 tight | 4k | 460 / 15 | 0.823 | 0.608 | 0.820 | 12/14 |
| g4-26b-a4b-qat | MoE | 13.45 (4.58) | 14.70 tight | 16k | 1893 / 59 | 0.902 | 0.633 | 0.860 | 14/14 |
| qwen3-30b-a3b-q3 | MoE | 13.70 (3.85) | 14.79 tight | 4k | 1910 / 80 | 0.854 | 0.617 | 0.860 | 14/14 |
| g4-26b-a4b-qat-mtp | MoE | 13.45 (4.58) | 15.06 **NO** | 8k | 1886 / 55 | — | — | — | 14/14 |

*Table 1 — the roster, sorted by footprint. `ok` = at least 1 GiB of headroom against a 15 GiB budget, `tight` = fits with less, `NO` = over budget. Effective bpw is computed from the file size and the parameter count the server reports, not from the file name. HumanEval at cap 512 (8192 for the thinking arm), MMLU-Pro at cap 512 (4096 for the thinking arm), IFEval at n=50 and the task's 1280 cap (4096 for the thinking arm). The MTP row has no quality axes: it is the same weights as `g4-26b-a4b-qat` plus a 0.43 GiB draft head, measured for speed and fit only.*

The rule that makes any of this a comparison: **matched family, matched quant family, one cap, one context policy, one build**. The controlled pair is `g4-12b-qat` (dense) against `g4-26b-a4b-qat` (MoE) — same tokenizer, same training recipe, both quantisation-aware at ~4.5 effective bpw. A Q4_K_M row against a QAT Q4_0 row would be a quantisation comparison wearing an architecture label.

## 2. What wins, on each axis and overall

Each axis has a different winner, and the model that wins overall is not the one that wins the cheap
axis. Counts are in items, not percentages, because that is what the sample supports.

| axis | winner | result | next best | reading |
|---|---|---|---|---|
| HumanEval pass@1 | lfm25-24b-a2b-think | 0.970 (159/164) | g4-26b-a4b-qat 0.902 (148/164) | 11 problems clear — the only decisive win in the roster |
| MMLU-Pro | lfm25-24b-a2b-think | 0.692 (83/120) | g4-26b-a4b-qat 0.633 (76/120) | 7 items against a ±8 confidence band: a shared top group, not a winner |
| IFEval strict | g4-12b-qat and lfm25-24b-a2b-think | 0.920 (46/50) | g4-e4b-qat and qwen3-8b-q4 at 0.900 (45/50) | exact tie; the next pair is one prompt behind |
| decode | lfm25-24b-a2b-think | 111 tok/s | qwen3-30b-a3b-q3 80 tok/s | the budget-0 arm of the same file is 110 tok/s, so this is one winner, not two |
| prefill | lfm25-24b-a2b-think | 3360 tok/s | g4-e4b-qat 2243 tok/s | fastest here, and the least portable number on the page |
| riddles | eight models tied | 14/14 | qwen3-8b-q4 and lfm25-24b-a2b at 13/14 | mistral-24b alone at 12/14 |
| quality per GiB | g4-e4b-qat | 0.138 mean/GiB | g4-12b-qat 0.104 | both beat every 13 GiB row on this measure |
| **overall** | **lfm25-24b-a2b-think** | **0.860 mean** | g4-26b-a4b-qat 0.799 | top or joint-top on all three quality axes, fastest decode and prefill, and it fits at 32k |

*Table 2 — the winners. "Overall" is the mean of HumanEval, MMLU-Pro and IFEval, which is a convenience, not a protocol: a coding workload should read the first row and ignore the last, and a knowledge workload the second.*

What that table means in practice:

- **lfm25-24b-a2b with deliberation on is the model to run if the card has 14 GiB to spare.** It is the
  only row that wins an axis outright (HumanEval, by 11 items), it is joint-first on instruction-following,
  it leads decode and prefill, and it does all of it inside a 32k context. Two costs are real: it
  deliberates before answering, so the throughput lead is decode rate and not time-to-answer; and the same
  weight file with reasoning disabled (`lfm25-24b-a2b`) is the worst knowledge row in the roster at 0.192.
  Never quote the file without naming the arm.
- **g4-12b-qat is the model to run if half the memory matters.** It is joint-first on IFEval, second among
  dense models on HumanEval, and its mean quality is a statistical tie with the 26B MoE (0.797 against
  0.799) at 52% of the footprint and twice the context.
- **g4-26b-a4b-qat is the knowledge pick.** It is the runner-up on both capability axes and the only model
  that clearly beats the 12B on MMLU-Pro (0.633 against 0.575), at 2.1x the decode rate — but it needs
  13.45 GiB and fits only 16k.
- **g4-e4b-qat is the only sane answer below 8 GiB.** 5.40 GiB, 0.866 HumanEval, 0.900 IFEval, 32k context.
  Its MMLU-Pro of 0.467 is the price, and it is a category drop, not a rounding difference.
- **Nobody wins on the 4k rows.** `mistral-24b-q4` and `qwen3-30b-a3b-q3` fit the card only at 4k context;
  the 30B is fast and knowledgeable enough to be interesting, and still loses on usability to a 12B that
  runs at 32k.

## 3. How to read the numbers

- **Quality does not depend on the GPU.** HumanEval, MMLU-Pro, IFEval, the needle probes and the protocol checks are all hardware-independent. They transfer to a card unchanged.
- **Decode ranks transfer, absolute rates do not.** Both platforms are bandwidth-bound on bytes read per token, so the ordering holds; the numbers scale with bandwidth, and the reference host sits at ~256 GB/s.
- **Prefill does not transfer at all.** It is compute-bound, and an MoE's prefill touches every expert that receives a token, so a discrete card pulls further ahead on exactly the rows where the numbers below look slowest.
- **Caps and sample sizes are part of the result.** HumanEval is 164 items (±2.3 points at a score of 0.90), MMLU-Pro 120 items (±4.4 at 0.61), IFEval 50 prompts (±3.8 at 0.92). Roughly eight points on IFEval or nine on MMLU-Pro is the smallest difference worth arguing about. MMLU-Pro here is a 0-shot chat probe, not the 5-shot loglikelihood protocol the public leaderboards use: the column is internally consistent and sits below published scores by design.

## 4. Quality against what the card has to hold

{{svg charts/16gb-f1.svg}}

*Figure 1 — Quality against footprint, with 95% confidence intervals. The shaded band and the dashed line mark a 16 GiB card's 15 GiB budget; the dotted line is the Pareto front (no model above it is both smaller and better). A point's horizontal position is weights plus its own KV cache, so a model with expensive attention sits further right than its file size suggests.*

Three things fall out of that figure.

**The best model in the class is not the biggest.** `lfm25-24b-a2b` with deliberation left on scores 0.970 / 0.692 / 0.920 at 13.96 GiB — top of the roster on every axis — and decodes at 111 tok/s. The same weights with reasoning disabled collapse to 0.640 / 0.192 / 0.860, a 50-point knowledge loss for the identical file. The arm has to be named whenever the row is quoted.

**Half the memory buys a statistical tie.** `g4-12b-qat` at 7.67 GiB scores 0.896 / 0.575 / 0.920 against the 26B MoE's 0.902 / 0.633 / 0.860. On the mean of the three axes that is 0.797 against 0.799 — and it keeps 32k of context where the 26B fits 16k.

**Two rows are a warning, not a candidate.** `mistral-24b-q4` and `qwen3-30b-a3b-q3` fit only at 4k context. At this footprint, capacity buys parameters at the cost of the context you need to use them.

## 5. Context is a second budget

Weights are the visible cost. KV cache is the one that decides whether the model is usable, and it is not proportional to model size — it follows the attention layout. On this roster a 14B dense model costs 160 MiB per 1k tokens of context while a 26B MoE costs 20.

| model | KV MiB per 1k tokens | KV at 8k | at 16k | at 32k | at 64k |
|---|---|---|---|---|---|
| g4-12b-qat | 16 | 0.06 | 0.12 | 0.25 | 0.50 |
| g4-26b-a4b-qat | 20 | 0.08 | 0.16 | 0.31 | 0.62 |
| lfm25-24b-a2b-think | 20 | 0.08 | 0.16 | 0.31 | 0.62 |
| gpt-oss-20b-mxfp4 | 24 | 0.09 | 0.19 | 0.38 | 0.75 |
| g4-e4b-qat | 28 | 0.11 | 0.22 | 0.44 | 0.88 |
| qwen3-30b-a3b-q3 | 48 | 0.19 | 0.38 | 0.75 | 1.50 |
| qwen3-8b-q4 | 144 | 0.56 | 1.12 | 2.25 | 4.50 |
| qwen3-14b-q4 | 160 | 0.62 | 1.25 | 2.50 | 5.00 |
| mistral-24b-q4 | 160 | 0.62 | 1.25 | 2.50 | 5.00 |

*Table 3 — KV cache cost in GiB, measured per model at q8_0 and halved from the fp16 figure by the loader's KV quantisation. This is why a 24B dense model is a 4k-context model on a 16 GiB card and a 26B MoE is a 16k-context model.*

{{svg charts/16gb-f2.svg}}

*Figure 2 — The largest context whose KV cache still fits 15 GiB, capped by each model's trained length. The tick on each bar is the context the roster actually measured at: in most cases the card can afford more than we ran.*

The practical rule: **when a model does not fit, cut context first, then KV precision, then quantisation depth, and only then offload.** Context is the cheapest thing to give up and the only one that costs no quality at all.

## 6. Dense or MoE

A dense model runs every parameter for every token. An MoE routes each token to a subset of experts, so a 26B model with 8 of 128 active does roughly the arithmetic of a 4B model while carrying 26B of weights. Footprint follows total parameters; decode speed follows active parameters; the two stop being proportional.

{{svg charts/16gb-f3.svg}}

*Figure 3 — Weights against decode rate on a log scale, coloured and shaped by class. The MoE band sits above the dense band at every size: `lfm25-24b-a2b-think` decodes at 111 tok/s on 12.65 GiB while `mistral-24b-q4` manages 14.9 on 13.35.*

{{svg charts/16gb-f4.svg}}

*Figure 4 — The controlled pair. Same family, same quantisation-aware ~4.5 bpw training, same caps, one box. Bars carry 95% confidence intervals; the difference on HumanEval is one problem and the difference on MMLU-Pro is seven.*

The honest reading is that neither is strictly better:

| axis | g4-12b-qat (dense, 6.26 GiB) | g4-26b-a4b-qat (MoE, 13.45 GiB) | verdict |
|---|---|---|---|
| HumanEval | 0.896 | 0.902 | one problem — tie |
| MMLU-Pro | 0.575 | 0.633 | MoE, 7 points — real |
| IFEval | 0.920 | 0.860 | dense, 3 prompts |
| decode | 27.8 tok/s | 59.2 tok/s | MoE, 2.1x |
| footprint | 7.67 GiB at 32k | 14.70 GiB at 16k | dense, 2x the context |

*Table 4 — the controlled pair. Choose the MoE when knowledge and throughput matter; choose the dense model when instruction-following, context or headroom matter.*

## 7. What a 16 GiB card can actually run

{{svg charts/16gb-f5.svg}}

*Figure 5 — How much of this roster fits at 8k context as the card grows, by pure arithmetic against a budget of (size − 1 GiB).*

| card | usable | models that fit at 8k | best of them by mean quality | what it means |
|---|---|---|---|---|
| 8 GB | 7 GiB | 2 of 11 | qwen3-8b-q4 | 4-8B dense only; every MoE in the roster is out |
| 12 GB | 11 GiB | 4 of 11 | g4-12b-qat | the dense 12B/14B tier arrives; nothing above 10 GiB fits |
| 16 GB | 15 GiB | 10 of 11 | lfm25-24b-a2b-think | the MoE tier arrives, and with it the best quality in the roster; the MTP arm is the one casualty |
| 24 GB | 23 GiB | 11 of 11 | lfm25-24b-a2b-think | everything here fits, at its context, with room for a second model |
| 32 GB+ | 31 GiB+ | 11 of 11 | lfm25-24b-a2b-think | this roster saturates; the limit is the roster, not the card |

*Table 5 — the ladder. The 32 GB and 48 GB columns are roster-limited, not card-limited: nothing here is larger than 13.9 GiB, so they say nothing about how a 32 GB card behaves with a 30 GiB model.*

The step from 12 GB to 16 GB is the one that matters. It is not a larger dense model that you gain — it is the MoE tier, and with it the only rows in this roster that score above 0.90 HumanEval while fitting at 32k context.

## 8. Quantisation on a fixed budget

Effective bits per weight is measured from the file, so the ladder below is arithmetic anchored on measured files rather than on vendor claims:

| weights budget (15 GiB less 1 GiB overhead) | 25B-class params at | fits? |
|---|---|---|
| ~13.6 GiB | 4.6 bpw | yes — this is exactly what `g4-26b-a4b-qat` is (13.45 GiB, 4.58 bpw) |
| ~13.6 GiB | 5.0 bpw | no — 15.6 GiB of weights |
| ~13.6 GiB | 3.9 bpw | yes, and leaves ~2 GiB of KV room — what `qwen3-30b-a3b-q3` does at 3.85 bpw |

*Table 6 — the quantisation ceiling on a 16 GiB card. Arithmetic from file size and parameter count; the budget shown excludes KV.*

Two observations from the measured rows rather than the arithmetic. First, QAT pays: the quantisation-aware `g4-12b-qat` reaches 0.896 HumanEval at 4.52 bpw, which no 4-bit post-training quant in this roster matches at that footprint. Second, going deeper costs knowledge unevenly — the 3.85 bpw 30B keeps 0.617 MMLU-Pro, but it only affords 13k of context, so on this card the trade is context, not accuracy.

## 9. When it does not fit

The MTP row is the useful failure: 15.06 GiB at 8k context, over budget by 0.06 GiB. That is what the wall looks like — not a crash, but a model that loads and then spends its life at the edge of the pool. In order of cost:

1. **Cut context.** Halving 32k to 16k returns 0.3-2.5 GiB depending on the model's attention layout (Table 3), and costs nothing in quality for prompts that fit.
2. **Quantise the KV cache.** q8_0 is already assumed throughout; q4_0 halves it again at a small quality cost and is the standard second lever.
3. **Drop the drafter.** A speculative-decoding head costs weights plus a second KV cache; on this roster it is 0.43 GiB and pushes a fitting model over the line.
4. **Drop quantisation depth.** One step down is roughly 0.5-1 GiB on a 25B model. It is the only lever that changes what the model knows.
5. **Offload layers.** `-ngl` below the layer count moves layers to CPU, which costs PCIe or system-memory bandwidth on every token — the 5-10x decode collapse that a discrete card shows on spill.

Flags that matter on this class, all used for every row above: `-ngl 99` (all layers on the GPU), `-c` set to the context you measured at rather than the model's maximum, `--flash-attn on`, `--cache-type-k q8_0 --cache-type-v q8_0`, `-np 1` (one slot — concurrency multiplies KV), `-b 4096 -ub 2048` for prefill batching. Nothing here is exotic; the discipline is that each of them changes what fits.

## 10. Three memory architectures

{{svg charts/16gb-f6.svg}}

*Figure 6 — Peak memory bandwidth on a log scale, with the PCIe spill path for comparison. Bandwidth sets decode; whether there is a hard ceiling at all decides what runs.*

- **Unified APU (this class of box).** 128 GB of LPDDR5X-8000 on a 256-bit bus, ~256 GB/s, with up to ~96 GiB GPU-addressable and an 8 GiB carve-out. No wall to cross, so a 40 GiB model runs — at the speed 256 GB/s allows.
- **Discrete card.** 24 GB at 1008 GB/s or 32 GB at 1792 GB/s: four to seven times the bandwidth on a fifth of the capacity. Over the VRAM limit, layers spill to host memory across PCIe (~64 GB/s on a 5.0 x16 link) and decode falls by roughly an order of magnitude. In this class the card is not capacity-constrained at all — the whole roster fits at 24 GB.
- **Apple Silicon.** Unified like the APU, with a wider bus: 546 GB/s on an M4 Max, 819 GB/s on an M3 Ultra, capacities from 36 GB to 512 GB. No hard wall, a driver-capped GPU share, and a Metal rather than CUDA/ROCm software path.

| quantity | transfers? | why |
|---|---|---|
| quality scores | yes, unchanged | depends on weights, quant, cap and prompt protocol only |
| decode ranking | yes | both platforms bandwidth-bound on bytes read per token |
| decode absolute rate | no | scale by bandwidth: 256 GB/s here against 1008-1792 GB/s on a card |
| prefill ranking | partly | dense-to-dense mostly holds; MoE prefill is understated here |
| prefill absolute rate | no | a card has far more compute per byte of bandwidth |
| fit | no | arithmetic against the target's own memory ceiling |
| needle, riddles, protocol | yes | nothing in the path touches the GPU pool |

*Table 7 — what may be carried from this page to another machine, and what may not.*

## 11. What this page does not measure

Listed because the gaps are the useful part of a benchmark:

- **Agentic tool use.** Preflight confirms an OpenAI-shaped client can read the reply (3/3 on every row: non-empty content, a JSON object, a one-word answer). A multi-round tool loop was not run, and a model can pass preflight and still fail to drive tools.
- **Long-context retrieval per model.** The roster's needle probes are at 2k and 8k. A depth curve to 100k+ was run for other models on this platform, not for these.
- **Energy and thermals per token.** Package power during a batch sat around 96 W with the GPU at 76 °C on the reference host, but that is a spot sample, not an energy-per-1k-tokens measurement.
- **Concurrency.** Every row was measured with one slot. Throughput under `-np 4` is a different measurement with a different KV footprint.
- **Quant ladders per model.** One quant per model was measured. The claim that QAT holds up better than post-training quant at equal bpw rests on the controlled pair, not on a sweep.
- **Real spill behaviour.** This host cannot show it. The spill penalty quoted for discrete cards is from the literature and the PCIe arithmetic, not from a measurement on a card.

## 12. Reproduce any row

The roster is one directory of stdlib scripts driving one llama.cpp server at a time:

```
cd ~/bench/16gb
python3 matrix.py list                  # roster, computed footprints, gap flags
python3 matrix.py budget --ctx 8192     # fit arithmetic at any context
python3 matrix.py run g4-12b-qat        # launch, core axes, stop
python3 matrix.py run g4-12b-qat --full # + HumanEval 164 / MMLU-Pro 120 / IFEval
python3 report.py                       # the joined table
```

```
# standalone full axes, which is how the caps stay controlled
python3 humaneval.py --port 8180 --limit 164 --max-tokens 8192
.venv/bin/lm-eval run --model local-chat-completions \
  --model_args model=local,base_url=http://127.0.0.1:8180/v1/chat/completions \
  --tasks ifeval --limit 50 --batch_size 1 --apply_chat_template \
  --gen_kwargs max_gen_toks=4096      # only for a deliberating model
```

Figures on this page are generated from the same run archive by `charts16.py`; the fit arithmetic in the tables is the expression `matrix.py budget` prints, so a figure and a table cannot disagree.

## 13. Document history

| version | date | what changed |
|---|---|---|
| 1.0 | 2026-11-10 | First release. Eleven files measured for the 16 GiB class on a host with no VRAM ceiling, three axes at stated caps, fit and KV arithmetic from the same roster file the runs used, six computed figures, the three-platform bandwidth comparison. |

*The version number belongs to this page. The wider report on this platform has its own history in
[the change log](changelog.html); a correction to a number here bumps the version above and states what the
previous value was, on the same rule the main report follows.*


---

*Source, data and build scripts: [github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io](https://github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io). Text, figures and data: CC BY 4.0.*
