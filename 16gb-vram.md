# 16 GiB of VRAM: which local LLMs fit, and what they score

- **Author:** Dom ([github.com/barmynon](https://github.com/barmynon)) · measurements, analysis and writing,
  with Hermes Agent (Nous Research) driven by DeepSeek `deepseek-flash`
- **Document version:** **1.17** · 10th November 2026 · Minor updates
- **Measured:** 10th November 2026 · 11 weight files, 113.8 GiB · one llama.cpp build, one KV setting, one slot
- **Axes:** HumanEval 164 items · MMLU-Pro 120 · IFEval 50 prompts · needle 2k/8k · riddles 14 · protocol 3
- **History of this page:** §16 · **Wider report on this platform:** [index.html](index.html)



A 16 GiB graphics card is the tightest interesting class of consumer accelerator: 16 GiB of VRAM, about 15 GiB usable once the driver and runtime have taken their share, and a hard wall at the end of it. This page answers two questions about that class. Which open-weight models fit, and what do they score. Then: how much of that answer depends on the memory architecture underneath, because the same 13.4 GiB file behaves very differently on a unified-memory APU, a discrete card and an Apple SoC.

Every number here was measured on a machine that does **not** have the constraint being studied. The reference host is a Minisforum MS-S1 MAX with no VRAM ceiling — a 100 GiB GTT window means nothing is truncated or spilled while it is being benchmarked. That is deliberate: the scores describe the model, the arithmetic describes the card, and the two are never confounded. Where a figure is arithmetic rather than measurement, it says so.

### What it ran on

Three of the numbers on this page — decode, prefill, and every footprint the fit arithmetic produces — are properties of the stack below as much as of the models, so the stack is stated rather than assumed.

| component | this host | why it is in the table |
|---|---|---|
| CPU | AMD Ryzen AI Max+ 395 (Zen 5), 16 cores / 32 threads, 625 MHz – 5.19 GHz, 64 MiB L3 | prompt handling and sampling run beside the GPU, so prefill is not a pure GPU rate |
| GPU | Radeon 8060S, RDNA 3.5 (`gfx1151`), 40 CUs | the only compute device; weights and ALUs share one memory, so there is no PCIe hop for a token to cross |
| memory | 128 GiB LPDDR5X-8000, 256-bit, unified: an 8 GiB UMA carve-out reported as VRAM, plus a 100 GiB GTT window (`ttm.pages_limit` 26,214,400 pages) | sets the ~256 GB/s decode ceiling (§11) and is the memory a footprint is held against; a 13.4 GiB file is resident in it, not paged from disk |
| storage | BIWIN X570 PRO 4TB NVMe, btrfs, `/home`: 771 GiB of weight files | weights are mmap'd once at load and then sit in the GTT window, so the disk sets load time and nothing else — direct reads measured 0.5-1.9 GB/s on this drive, about 10 s for the largest roster file. A slower disk would move no score on this page |
| OS | CachyOS (Arch-based, rolling), systemd 262, glibc 2.44 | it fixes the kernel build, the Mesa version and the CPU governor below; the same silicon on a stock distribution would be a different stack |
| kernel | 7.3.3 (CachyOS), `amdgpu`, `amd-pstate-epp` active, governor `powersave` with EPP `balance_performance` | the 100 GiB GTT window comes from a module option in `/etc/modprobe.d/ttm.conf`, not from a default, and its size decides whether a file stays resident; the pstate mode decides how far the 5.19 GHz boost is held under sustained load |
| graphics stack | Mesa 26.2.6, `vulkan-radeon` 26.2.6, Vulkan 1.4, RADV (`STRIX_HALO`) | llama.cpp's Vulkan backend is what executes, so a driver change moves every rate here |
| inference build | llama.cpp fork, build `b3-1a33095` (0.5.0-dev, commit 1a33095), `ggml-vulkan` ABI 0.25.3, clean tree | one program for all eleven files: no row is a different build |
| server flags | `-ngl 99`, `-c` per model, `--flash-attn on`, `--jinja`, KV cache `q8_0` on both K and V, `-b 4096 -ub 2048`, one slot (`-np 1`); speculative decoding off except on the MTP row; reasoning off with a zero budget on `lfm25-24b-a2b` | one context and batching policy for every row, and the `q8_0` KV is why §6 halves the fp16 figure |
| telemetry | the host's own monitor: CPU `Tctl/Tdie` to 0.1 °C, GPU temperature in 1 °C steps, CPU package power and GPU PPT, sampled every ~2 s, raw kept 72 h and 1-minute rollups for 90 days | every run can be re-read against its temperatures and power draw; the ranges quoted under this table come from it, not from a spot check |
*Table 1 — the platform. Every number on this page comes off this stack; the right-hand column says which measurements would move if a part of it changed, and which are properties of the models alone.*

Power and temperature are logged, not assumed: the host's own monitor samples CPU and GPU temperature and package power every couple of seconds, so every run can be read back against its thermals. Across the 24 runs long enough to have a measured window, GPU temperature averaged 69 °C against a hottest run average of 79 °C and a hottest single sample of 88 °C, and package power averaged 96 W with a peak of 129 W. No run applied a power cap — the SoC pulls what its firmware allows — so the throughput columns are this box's behaviour rather than a ceiling for the silicon.

The other thing this table does not claim is that the host is representative of the class it measures. It has no 16 GiB wall at all: the card being studied here is a budget applied in arithmetic, not a device, which is exactly why the measurements were taken on it.



Eleven files, 164-item HumanEval, 120-item MMLU-Pro, 50-prompt IFEval, 113.8 GiB of weights, one build.

> **Also published:** [the main report](index.html) — the wider model matrix on this platform · [leaderboards by axis](leaderboards.html) · [retired models](retired.html) · [change log](changelog.html).

## 1. The roster

| model | class | weights GiB (bpw) | footprint at its context | context | pp / tg t/s | HumanEval | MMLU-Pro | IFEval | mean quality | quality per GiB | riddles |
|---|---|---|---|---|---|---|---|---|---|---|---|
| g4-e4b-qat | dense | 3.93 (4.52) | 5.40 ok | 32k | 2243 / 58 | 0.866 | 0.467 | 0.900 | 0.744 | 0.138 | 14/14 |
| qwen3-8b-q4 | dense | 4.68 (4.91) | 7.93 ok | 32k | 1300 / 39 | 0.787 | 0.583 | 0.900 | 0.757 | 0.095 | 13/14 |
| g4-12b-qat | dense | 6.26 (4.52) | 7.67 ok | 32k | 911 / 28 | 0.896 | 0.575 | 0.920 | 0.797 | 0.104 | 14/14 |
| qwen3-14b-q4 | dense | 8.38 (4.87) | 10.63 ok | 16k | 743 / 24 | 0.854 | 0.608 | 0.880 | 0.781 | 0.073 | 14/14 |
| gpt-oss-20b-mxfp4 | MoE | 11.28 (4.63) | 12.65 ok | 32k | 2169 / 74 | 0.585 | 0.558 | 0.480 | 0.541 | 0.043 | 14/14 |
| lfm25-24b-a2b | MoE | 12.65 (4.53) | 13.96 ok | 32k | 3345 / 110 | 0.640 | 0.192 | 0.860 | 0.564 | 0.040 | 13/14 |
| lfm25-24b-a2b-think | MoE | 12.65 (4.53) | 13.96 ok | 32k | 3360 / 111 | 0.970 | 0.692 | 0.920 | 0.860 | 0.062 | 14/14 |
| mistral-24b-q4 | dense | 13.35 (4.86) | 14.66 tight | 4k | 460 / 15 | 0.823 | 0.608 | 0.820 | 0.751 | 0.051 | 12/14 |
| g4-26b-a4b-qat | MoE | 13.45 (4.58) | 14.70 tight | 16k | 1893 / 59 | 0.902 | 0.633 | 0.860 | 0.799 | 0.054 | 14/14 |
| qwen3-30b-a3b-q3 | MoE | 13.70 (3.85) | 14.79 tight | 4k | 1910 / 80 | 0.854 | 0.617 | 0.860 | 0.777 | 0.053 | 14/14 |
| g4-26b-a4b-qat-mtp | MoE | 13.45 (4.58) | 15.06 **NO** | 8k | 1886 / 55 | — | — | — | — | — | 14/14 |

*Table 2 — the roster, sorted by footprint. `ok` = at least 1 GiB of headroom against a 15 GiB budget, `tight` = fits with less, `NO` = over budget. Effective bpw is computed from the file size and the parameter count the server reports, not from the file name. HumanEval at cap 512 (8192 for the thinking arm), MMLU-Pro at cap 512 (4096 for the thinking arm), IFEval at n=50 and the task's 1280 cap (4096 for the thinking arm). Mean quality and quality per GiB are the two derived rows of §2: the first is the average of the three scores to its left, the second divides that average by the footprint column — not by the weights, which is the error that makes a big-context model look cheap. Neither is a measurement, and neither carries a cap of its own. The MTP row has no quality axes: it is the same weights as `g4-26b-a4b-qat` plus a 0.43 GiB draft head, measured for speed and fit only. What each column measures, and what it cannot tell you, is §2.*

The rule that makes any of this a comparison: **matched family, matched quant family, one cap, one context policy, one build**. The controlled pair is `g4-12b-qat` (dense) against `g4-26b-a4b-qat` (MoE) — same tokenizer, same training recipe, both quantisation-aware at ~4.5 effective bpw. A Q4_K_M row against a QAT Q4_0 row would be a quantisation comparison wearing an architecture label.

## 2. What the evaluation axes actually measure

Every quality number on this page comes from one of three public benchmarks, run here at a stated sample
size and a stated token cap. They measure different things and they fail in different ways, so a table of
scores is unreadable without knowing which one a column is.

| axis | what the model is asked to do | how it is scored | what was run here | what it does not tell you |
|---|---|---|---|---|
| HumanEval | 164 short Python problems: a docstring and a signature, write the function body | the generated code is executed against unit tests; pass@1 is the fraction passing on the first attempt at temperature 0 | 164 items, complete-program prompt, cap 512 (8192 for the thinking arm) | other languages, multi-file work, debugging, or whether it can drive a tool |
| MMLU-Pro | multiple-choice questions over 14 academic domains, 10 options rather than 4, so guessing pays less than on MMLU | the answer letter is parsed out of a chat completion, 0-shot — no worked examples | 120 items, 0-shot chat probe, cap 512 (4096 for the thinking arm) | reasoning depth, recency or calibration; it is a knowledge quiz, not a task |
| IFEval | prompts carrying mechanically checkable constraints — "more than 400 words", "exactly 5 bullet points", "in JSON", "end with this phrase" | code checks each constraint: strict is exact text, loose allows whitespace and quote normalisation; prompt level means every constraint met, instruction level is the per-constraint average | 50 prompts at the task's own 1280-token cap (4096 for the thinking arm) | whether the content is right, or whether it obeys constraints nobody spelled out |
| prefill and decode (pp / tg) | the same server under load: a 2000-token prompt in, then generation out | tokens per second from the server's own counters, one slot | one measurement per model, one context, one build | batch throughput, power, or what a card would do — §4 and §12 cover transfer |
| riddles | 14 short arithmetic and logic probes | exact match, with a retry at four times the cap when the model ran out mid-answer, so the cap is not scored as a wrong answer | 14 probes at temperature 0.2 | anything statistical: it is a smoke test for gross failure, not an axis |
| **mean quality** *(derived)* | nothing is run — it is the average of the three quality scores | `(HumanEval + MMLU-Pro + IFEval) / 3`, computed from the rows above | every model that has all three axes; the MTP row has none | that a model is good at any one thing. It is a sorting device, not a score, and it hides which axis a model is actually good at |
| **quality per GiB** *(derived)* | nothing is run either — it is that mean divided by the model's footprint | `mean quality ÷ footprint at its own context`, in GiB | footprint, not weights: the number the card actually spends | that a model is good. A cheap model can top this rank while scoring badly — which is exactly what the budget pick does, at 0.744 mean and 0.138 per GiB |

*Table 3 — the axes, as they were actually run, plus the two derived numbers the tables lean on. Sample size and cap belong to the result: a HumanEval row at 512 and one at 8192 are not the same measurement, and §4 explains what that costs in confidence. The derived rows have no cap of their own and inherit the caps of what they average.*

### Cap, budget, and what the budget is spent on

Every number on this page is qualified by one of these, so they are worth fixing before the scores.

- **cap** — the maximum number of tokens the model was allowed to generate for a single answer
  (`max_tokens` in a chat request, `max_gen_toks` in lm-eval). It is part of the measurement, not a
  setting: the same model at cap 512 and at 8192 is two different results, and a deliberating model at a
  small cap produces no answer at all — the reasoning block eats the budget and the failure reads as a
  wrong answer rather than a truncated one. Wherever a cap is unusual it is printed in the row and in the
  figure caption, because a score without its cap cannot be compared with anything.
- **budget** — the memory a card can actually spend: **15 GiB on a 16 GiB card**, after the driver and
  runtime have taken their share. Weights, the KV cache for the context, and about 1 GiB of runtime
  overhead all have to fit inside it. A model over budget does not run slowly, it does not run — so fit is
  settled before speed is discussed, and every table marks it: `ok` = at least 1 GiB of headroom left,
  `tight` = fits with less, `NO` = over budget.
- **footprint** — how much of that budget a model actually takes: weights, plus KV at the context it is
  run at, plus the 1 GiB overhead. It is why a 6.26 GiB file can occupy 7.67 GiB, and why the same file at
  32k costs more than at 8k.
- **KV cache** — per-conversation memory for attention. It grows linearly with context and is set by the
  model's attention layout, not its size: on this roster a 14B dense model costs 160 MiB per 1k tokens
  against a 26B MoE's 20 — attention layout, not size, sets the bill (§6).

None of these is a preference. Cap is a fact about the run, budget is arithmetic about the card, footprint
and KV are what the arithmetic is spent on.

Each axis can also be satisfied without doing the thing it is named after — which is the part that makes the
roster disagree with itself:

- **HumanEval rewards code shape.** 0.90 here and the model may still be unable to say why the function works.
- **MMLU-Pro rewards discrimination between near-neighbours.** Know the topic, miss the distinction, and the
  score is indistinguishable from knowing neither.
- **IFEval rewards compliance.** Format it correctly and the marks are yours even when the content is wrong.

That is why the winners differ by axis (§3), and why the "mean of the three" is a sorting device rather than
a claim that a model is 0.86 good. Read the column that matches your workload; read the mean only to order a
shortlist.

## 3. What wins, on each axis and overall

Each axis has a different winner, and the model that wins overall is not the one that wins the cheap
axis. Counts are in items, not percentages, because that is what the sample supports.

| axis | winner | result | next best | reading |
|---|---|---|---|---|
| HumanEval pass@1 | lfm25-24b-a2b-think | 0.970 (159/164) | g4-26b-a4b-qat 0.902 (148/164) | 11 problems clear — the only decisive win in the roster |
| MMLU-Pro | lfm25-24b-a2b-think | 0.692 (83/120) | g4-26b-a4b-qat 0.633 (76/120) | 7 items against a ±8 confidence band: a shared top group, not a winner |
| IFEval strict | g4-12b-qat and lfm25-24b-a2b-think | 0.920 (46/50) | g4-e4b-qat and qwen3-8b-q4 at 0.900 (45/50) | exact tie; the next pair is one prompt behind |
| decode | lfm25-24b-a2b-think | 111 tok/s | lfm25-24b-a2b 110 tok/s | the budget-0 arm of the same file at 110 — one file, so one winner, but the next-best column names the arm |
| prefill | lfm25-24b-a2b-think | 3360 tok/s | g4-e4b-qat 2243 tok/s | fastest here, and the least portable number on the page |
| riddles | eight models tied | 14/14 | qwen3-8b-q4 and lfm25-24b-a2b at 13/14 | mistral-24b alone at 12/14 |
| quality per GiB *(derived, §2)* | g4-e4b-qat | 0.138 mean/GiB | g4-12b-qat 0.104 | both beat every 13 GiB row on this measure |
| **overall** | **lfm25-24b-a2b-think** | **0.860 mean** | g4-26b-a4b-qat 0.799 | top or joint-top on all three quality axes, fastest decode and prefill, and it fits at 32k |

*Table 4 — the winners. "Overall" is the mean of HumanEval, MMLU-Pro and IFEval, which is a convenience, not a protocol: a coding workload should read the first row and ignore the last, and a knowledge workload the second.*

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

## 4. How to read the numbers

- **Quality does not depend on the GPU.** HumanEval, MMLU-Pro, IFEval, the needle probes and the protocol checks are all hardware-independent. They transfer to a card unchanged.
- **Decode ranks transfer, absolute rates do not.** Decode is bandwidth-bound on bytes read per token on all three architectures this page compares — the unified APU, a discrete card, an Apple SoC — so the ordering survives the hop even though the rates do not: the MS-S1 MAX sits at ~256 GB/s against 288-896 GB/s on a 16 GB card and 546-819 GB/s on Apple silicon.
- **Prefill does not transfer at all.** It is compute-bound, and an MoE's prefill touches every expert that receives a token, so a discrete card pulls further ahead on exactly the rows where the numbers below look slowest.
- **Caps and sample sizes are part of the result.** One standard error is ±2.3 points on HumanEval (164 items at a score of 0.90), ±4.5 on MMLU-Pro (120 at 0.61) and ±3.8 on IFEval (50 prompts at 0.92). Twice those — roughly eight points on IFEval, nine on MMLU-Pro — is the smallest difference worth arguing about. The whiskers on Figures 1 and 4 are 95% **confidence intervals** — the range the score would fall in on a fresh sample of the same size, computed as ±1.96 × √(p(1-p)/n) over the item count, which is about double the standard errors quoted here. That is what "95% CI" in those chart titles means: the text quotes one standard error, the charts draw 95% intervals, and both say which they are so a number cannot be read in the wrong units. MMLU-Pro here is a 0-shot chat probe, not the 5-shot loglikelihood protocol the public leaderboards use: the column is internally consistent and sits below published scores by design.

## 5. Quality against what the card has to hold

{{svg charts/16gb-f1.svg}}

*Figure 1 — Quality against footprint, with 95% confidence intervals. The shaded band and the dashed line mark a 16 GiB card's 15 GiB budget; the dotted line is the Pareto front (no model above it is both smaller and better). A point's horizontal position is its footprint — weights plus its own KV cache plus the 1 GiB overhead (§2) — so a model with expensive attention sits further right than its file size suggests.*

Three things fall out of that figure.

**The best model in the class is not the biggest.** `lfm25-24b-a2b` with deliberation left on scores 0.970 / 0.692 / 0.920 at 13.96 GiB — top of the roster on every axis — and decodes at 111 tok/s. The same weights with reasoning disabled collapse to 0.640 / 0.192 / 0.860, a 50-point knowledge loss for the identical file. The arm has to be named whenever the row is quoted.

**Half the memory buys a statistical tie.** `g4-12b-qat` at 7.67 GiB scores 0.896 / 0.575 / 0.920 against the 26B MoE's 0.902 / 0.633 / 0.860. On the mean of the three axes that is 0.797 against 0.799 — and it keeps 32k of context where the 26B fits 16k.

**Two rows are a warning, not a candidate.** `mistral-24b-q4` and `qwen3-30b-a3b-q3` fit only at 4k context. At this footprint, capacity buys parameters at the cost of the context you need to use them.

## 6. Context is a second budget

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

*Table 5 — KV cache cost in GiB, measured per model at q8_0 and halved from the fp16 figure by the loader's KV quantisation. This is why a 24B dense model is a 4k-context model on a 16 GiB card and a 26B MoE is a 16k-context model.*

{{svg charts/16gb-f2.svg}}

*Figure 2 — The largest context whose KV cache still fits 15 GiB, capped by each model's trained length. The tick on each bar is the context the roster actually measured at: in most cases the card can afford more than we ran.*

The practical rule: **when a model does not fit, cut context first, then KV precision, then quantisation depth, and only then offload.** Context is the cheapest thing to give up and the only one that costs no quality at all.

## 7. Dense or MoE

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
| **mean quality** *(derived)* | 0.797 | 0.799 | 0.002 — a tie, and it hides opposite directions |
| **quality per GiB** *(derived)* | 0.104 | 0.054 | dense, 1.9x — memory is what the tie costs |
| decode | 27.8 tok/s | 59.2 tok/s | MoE, 2.1x |
| footprint | 7.67 GiB at 32k | 14.70 GiB at 16k | dense, 2x the context |

*Table 6 — the controlled pair. Choose the MoE when knowledge and throughput matter; choose the dense model when instruction-following, context or headroom matter. The two derived rows say what the mean cannot: at 0.002 apart the pair is tied on average quality while disagreeing by 7 points on knowledge and 3 prompts on instruction-following, and the tie costs 1.9x the memory.*

## 8. What a 16 GiB card can actually run

{{svg charts/16gb-f5.svg}}

*Figure 5 — How much of this roster fits at 8k context as the card grows, by pure arithmetic against a budget of (size − 1 GiB).*

| card | usable | models that fit at 8k | best of them by mean quality | what it means |
|---|---|---|---|---|
| 8 GB | 7 GiB | 2 of 11 | qwen3-8b-q4 | 4-8B dense only; every MoE in the roster is out |
| 12 GB | 11 GiB | 4 of 11 | g4-12b-qat | the dense 12B/14B tier arrives; nothing above 10 GiB fits |
| 16 GB | 15 GiB | 10 of 11 | lfm25-24b-a2b-think | the MoE tier arrives, and with it the best quality in the roster; the MTP arm is the one casualty |
| 24 GB | 23 GiB | 11 of 11 | lfm25-24b-a2b-think | everything here fits, at its context, with room for a second model |
| 32 GB+ | 31 GiB+ | 11 of 11 | lfm25-24b-a2b-think | this roster saturates; the limit is the roster, not the card |

*Table 7 — the ladder. The 32 GB and 48 GB columns are roster-limited, not card-limited: nothing here is larger than 13.9 GiB, so they say nothing about how a 32 GB card behaves with a 30 GiB model.* Quality per GiB is deliberately not a column here: at every rung its winner is `g4-e4b-qat`, the smallest file, because the metric divides by footprint — which answers "what is cheapest per gigabyte", not "what is the best that fits". The column is the best that fits.

The step from 12 GB to 16 GB is the one that matters. It is not a larger dense model that you gain — it is the MoE tier, and with it the only row in this roster that scores above 0.90 HumanEval while fitting at 32k context.

{{svg charts/16gb-f6.svg}}

*Figure 6 — The decision map: mean of the three quality axes against footprint, with the 15 GiB budget drawn as a wall and a 0.78 competitive line drawn across. The three rings are the shortlist, and they are deliberately not the three highest dots — the budget pick sits below the line because it costs 5.4 GiB. Both lines are stated thresholds, not statistics: at 0.79 only two models clear the bar, at 0.75 seven do. There is no median crosshair and no upper-right "leader" corner, because here smaller footprint and higher score are both good, which a quadrant cannot express.*

The map is the one place where the three recommendations can be seen at once: the quality pick at the
top-right extreme, the value pick at roughly half its footprint, and the budget pick below the line at a
third of it. Everything else in the roster is either under the line, over the wall, or
both.

## 9. Quantisation on a fixed budget

Effective bits per weight is measured from the file, so the ladder below is arithmetic anchored on measured files rather than on vendor claims:

| weights budget (15 GiB less 1 GiB overhead) | 25B-class params at | fits? |
|---|---|---|
| ~13.6 GiB | 4.6 bpw | yes — this is exactly what `g4-26b-a4b-qat` is (13.45 GiB, 4.58 bpw) |
| ~13.6 GiB | 5.0 bpw | no — 15.6 GiB of weights |
| ~13.6 GiB | 3.9 bpw | yes, and leaves ~2 GiB of KV room — what `qwen3-30b-a3b-q3` does at 3.85 bpw |

*Table 8 — the quantisation ceiling on a 16 GiB card. Arithmetic from file size and parameter count; the budget shown excludes KV.*

Two observations from the measured rows rather than the arithmetic. First, QAT pays: the quantisation-aware `g4-12b-qat` reaches 0.896 HumanEval at 4.52 bpw, which no 4-bit post-training quant in this roster matches at that footprint. Second, going deeper costs knowledge unevenly — the 3.85 bpw 30B keeps 0.617 MMLU-Pro, but it only affords 4k of context, so on this card the trade is context, not accuracy.

## 10. When it does not fit

The MTP row is the useful failure: 15.06 GiB at 8k context, over budget by 0.06 GiB. That is what the wall looks like — not a crash, but a model that loads and then spends its life at the edge of the pool. In order of cost:

1. **Cut context.** Halving 32k to 16k returns 0.1-1.25 GiB depending on the model's attention layout (Table 5), and costs nothing in quality for prompts that fit.
2. **Quantise the KV cache.** q8_0 is already assumed throughout; q4_0 halves it again at a small quality cost and is the standard second lever.
3. **Drop the drafter.** A speculative-decoding head costs weights plus a second KV cache; on this roster it is 0.43 GiB and pushes a fitting model over the line.
4. **Drop quantisation depth.** One step down is roughly 0.5-1 GiB on a 25B model. It is the only lever that changes what the model knows.
5. **Offload layers.** `-ngl` below the layer count moves layers to CPU, which costs PCIe or system-memory bandwidth on every token — the 5-10x decode collapse that a discrete card shows on spill.

Flags that matter on this class, all used for every row above: `-ngl 99` (all layers on the GPU), `-c` set to the context you measured at rather than the model's maximum, `--flash-attn on`, `--cache-type-k q8_0 --cache-type-v q8_0`, `-np 1` (one slot — concurrency multiplies KV), `-b 4096 -ub 2048` for prefill batching. Nothing here is exotic; the discipline is that each of them changes what fits.

## 11. Three memory architectures

{{svg charts/16gb-f7.svg}}

*Figure 7 — Peak memory bandwidth on a log scale, with the PCIe spill path for comparison. Bandwidth sets decode; whether there is a hard ceiling at all decides what runs.*

- **Unified APU (this class of box).** 128 GiB of LPDDR5X-8000 on a 256-bit bus, ~256 GB/s, with a 100 GiB GTT window on top of an 8 GiB carve-out. No wall to cross, so a 40 GiB model runs — at the speed 256 GB/s allows.
- **Discrete card.** 24 GB at 1008 GB/s or 32 GB at 1792 GB/s: four to seven times the bandwidth on a fifth of the capacity. Over the VRAM limit, layers spill to host memory across PCIe (~64 GB/s on a 5.0 x16 link) and decode falls by roughly an order of magnitude. In this class the card is not capacity-constrained at all — the whole roster fits at 24 GB.
- **Apple Silicon.** Unified like the APU, with a wider bus: 546 GB/s on an M4 Max, 819 GB/s on an M3 Ultra, capacities from 36 GB to 512 GB. No hard wall, a driver-capped GPU share, and a Metal rather than CUDA/ROCm software path.

| quantity | transfers? | why |
|---|---|---|
| quality scores | yes, unchanged | depends on weights, quant, cap and prompt protocol only |
| decode ranking | yes | bandwidth-bound on bytes read per token on all three architectures, so the ordering holds |
| decode absolute rate | no | scale by bandwidth: 256 GB/s here against 1008-1792 GB/s on a card |
| prefill ranking | partly | dense-to-dense mostly holds; MoE prefill is understated here |
| prefill absolute rate | no | a card has far more compute per byte of bandwidth |
| fit | no | arithmetic against the target's own memory ceiling |
| needle, riddles, protocol | yes | nothing in the path touches the GPU pool |

*Table 9 — what may be carried from this page to another machine, and what may not.*

## 12. Which 16 GiB card, and what it implies

Every card in this class has the same 16 GB of VRAM, so **capacity decides nothing between them — bandwidth
decides everything**, and within the class bandwidth spans 3.1x. That single number is the purchase decision.
The spread is not a brand story: AMD's seven 16 GB boards run from 288 to 640 GB/s, NVIDIA's four from 288 to 896, Intel's one entry sits at 560.

| card | memory | peak bandwidth | 26B-A4B MoE, predicted | 12B dense, predicted |
|---|---|---|---|---|
| Minisforum MS-S1 MAX (reference) | unified LPDDR5X-8000, 256-bit | 256 GB/s | **59 tok/s measured** | **28 tok/s measured** |
| NVIDIA RTX 4060 Ti 16 GB | 128-bit GDDR6, 18 Gbps | 288 GB/s | 44-69 | 24-33 |
| AMD RX 7600 XT 16 GB | 128-bit GDDR6, 18 Gbps | 288 GB/s | 44-69 | 24-33 |
| AMD RX 9060 XT 16 GB | 128-bit GDDR6, 20 Gbps | 320 GB/s | 49-77 | 26-37 |
| NVIDIA RTX 5060 Ti 16 GB | 128-bit GDDR7, 28 Gbps | 448 GB/s | 68-108 | 37-52 |
| AMD RX 6800 16 GB | 256-bit GDDR6, 16 Gbps | 512 GB/s | 78-123 | 42-59 |
| Intel Arc A770 16 GB | 256-bit GDDR6, 17.5 Gbps | 560 GB/s | 86-134 | 46-65 |
| AMD RX 6950 XT 16 GB | 256-bit GDDR6, 18 Gbps | 576 GB/s | 88-138 | 47-67 |
| AMD RX 7900 GRE 16 GB | 256-bit GDDR6, 18 Gbps | 576 GB/s | 88-138 | 47-67 |
| AMD RX 7800 XT 16 GB | 256-bit GDDR6, 19.5 Gbps | 624 GB/s | 95-150 | 51-72 |
| AMD RX 9070 16 GB | 256-bit GDDR6, 20 Gbps | 640 GB/s | 98-154 | 52-74 |
| NVIDIA RTX 4070 Ti Super 16 GB | 256-bit GDDR6X, 21 Gbps | 672 GB/s | 103-161 | 55-78 |
| NVIDIA RTX 5070 Ti 16 GB | 256-bit GDDR7, 28 Gbps | 896 GB/s | 137-215 | 73-104 |

*Table 10 — 16 GB cards, vendor bandwidth, and the decode range it implies for the two models that matter here: the 13.45 GiB MoE (2.29 GB read per token) and the 6.26 GiB dense 12B (6.73 GB read per token). Bandwidth is the peak published in each card's own specification; every predicted figure is an extrapolation, not a measurement, and only the reference row is measured. Cards are grouped by bandwidth, not by brand.*

How the prediction is made, so it can be checked and discounted: decode is bandwidth-bound, so
`predicted = bandwidth / bytes-read-per-active-token × efficiency`, where efficiency is the fraction of the
ceiling the hardware actually reaches. The MS-S1 MAX measures 53% of its own ceiling on the MoE (59 of 111
tok/s) and 73% on the dense model (28 of 38). The bands in Table 10 use 35-55% for the MoE and 55-78% for the
dense model — deliberately wide, because a discrete card's kernels and a 128-bit card's higher latency per
byte will not match the MS-S1 MAX's Vulkan path exactly. Both measured values sit inside their bands, which
is the only calibration available without borrowing a card.

Three things follow, and one warning:

- **A 128-bit 16 GB card buys capacity at the cost of speed.** The four 128-bit boards — RTX 4060 Ti and RX
  7600 XT at 288 GB/s, RX 9060 XT at 320, RTX 5060 Ti at 448 — are the cheapest ways to hold 16 GB, and they
  decode at 0.75-1.85x the MS-S1 MAX. If the plan is "run a 13 GiB MoE", they hold it and they run it slowly.
- **The 256-bit cards are where the value is for this workload.** 512-672 GB/s covers the RX 6800, the Arc
  A770, the RX 6950 XT / 7900 GRE / 7800 XT / 9070 and the 4070 Ti Super: 1.3-2.7x the MS-S1 MAX's decode for
  the same 16 GB, which turns the 26B MoE from usable into comfortable. AMD is the wider choice here — five
  boards between 512 and 640 GB/s, with NVIDIA's nearest the 4070 Ti Super at 672.
- **The 5070 Ti is the top of the class and pays for it.** 896 GB/s is 3.5x the MS-S1 MAX, and it is the only
  16 GB card here whose dense-model band sits fully above 70 tok/s.
- **Warning: bandwidth does not buy prefill in the same proportion.** These predictions cover decode only.
  Prefill is compute-bound and an MoE's prefill touches every expert, so every card in this table will beat
  its decode-side prediction on long prompts by a margin the MS-S1 MAX cannot show — the same caveat that
  applies to Table 9. On the AMD side the software path matters too: these cards run through ROCm or Vulkan
  on Linux, and backend efficiency, not the memory spec, is what moves prefill.

{{svg charts/16gb-f8.svg}}

*Figure 8 — Left: vendor bandwidth for the 16 GB cards, against the MS-S1 MAX measured at 256 GB/s. Right: the decode band each bandwidth implies for the two reference models, with the MS-S1 MAX's measured points marked. The bars are a prediction from measured efficiency; the markers are the only measurements on the page.*

## 13. What this page does not measure

Listed because the gaps are the useful part of a benchmark:

- **Agentic tool use.** Preflight confirms an OpenAI-shaped client can read the reply (3/3 on every row: non-empty content, a JSON object, a one-word answer). A multi-round tool loop was not run, and a model can pass preflight and still fail to drive tools.
- **Long-context retrieval per model.** The roster's needle probes are at 2k and 8k. A depth curve to 100k+ was run for other models on this platform, not for these.
- **Energy and thermals per token.** Package power during a batch sat around 96 W with the GPU at 76 °C on the MS-S1 MAX; the monitor records that as a trace at ~2 s, so it is a thermal record rather than a spot sample — but it is still not an energy-per-1k-tokens measurement, which would need the integral.
- **Concurrency.** Every row was measured with one slot. Throughput under `-np 4` is a different measurement with a different KV footprint.
- **Quant ladders per model.** One quant per model was measured. The claim that QAT holds up better than post-training quant at equal bpw rests on the controlled pair, not on a sweep.
- **Real spill behaviour.** This host cannot show it. The spill penalty quoted for discrete cards is from the literature and the PCIe arithmetic, not from a measurement on a card.

## 14. Reproduce any row

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

Figures on this page are generated from the same run archive by `charts16.py`; the fit arithmetic in the tables is the expression `matrix.py budget` prints, so a figure and a table cannot disagree. The machine, build and server flags are the table at the top of the page; nothing in that stack is a variable in the commands above.

## 15. Licence

Everything on this page — the prose, the tables, the figures and the selection of measurements behind
them — is published under **[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)**. You may copy it,
quote it, republish it and build on it, including commercially, provided you credit it, link the licence
and say what you changed. The attribution line to use:

```
16 GiB of VRAM: which local LLMs fit, and what they score — strix-halo-128-benchmarks,
CC BY 4.0, https://strix-halo-128-benchmarks.github.io/16gb.html
```

That is worth stating precisely, because "a licence on information" is only partly possible:

- **What is licensed is the expression and the compilation**, not the facts. Nobody owns the measurement
  that this 26B MoE scores 0.902 on HumanEval at cap 512: you can re-measure it, quote the number, and
  disagree with it in public without asking anyone. The licence binds you when you copy the *page*, the
  *figures* or a substantial part of the *dataset*.
- **The database right is licensed too.** In the UK and the EU a collection of measurements can carry a
  separate sui generis right against extraction and re-utilisation even when individual facts are free.
  CC BY 4.0 covers that right explicitly, so bulk reuse of the rows is permitted with attribution rather
  than silently allowed.
- **It is not a warranty and not a patent grant.** The numbers are one machine, one build, stated caps;
  the licence gives you no assurance they describe your hardware, and CC licences grant no patent rights.
- **Model weights are not distributed here.** Every file named on this page carries its own licence from
  its publisher, and nothing on this page changes it — check the model card before you redistribute
  weights.
- **The benchmarks belong to their authors.** HumanEval, MMLU-Pro and IFEval are run against this box, not
  republished; cite the papers when you cite the scores.
- **The scripts in the repository are covered by the same licence**, because that is what its `LICENSE`
  file says. CC BY is written for prose and gives no patent grant, so if the intent is for other people to
  reuse the harness, a code-specific licence (MIT or Apache-2.0) for `scripts/` and `tools/` is the better
  split.

The copyright holder is Dom ([github.com/barmynon](https://github.com/barmynon)); the repository's `CITATION.cff` carries the citable form of that attribution.

The machine-readable form is alongside the page: a `license` field in the page's JSON-LD, a `rel="license"`
link in the document head, and the same CC BY 4.0 statement in the repository's `LICENSE` file.

## 16. Document history

| version | date | what changed |
|---|---|---|
| 1.17 | 10th November 2026 | Corrections pass: the 30B's context in §9 read 13k, it is 4k; §12 counted three NVIDIA boards, Table 10 lists four; the 128-bit decode multiplier read 0.9-1.8x, it is 0.75-1.85x, and the 256-bit group 2.0-2.6x, it is 1.3-2.7x; §10's halving claim read 0.3-2.5 GiB against Table 5's q8_0 columns, which give 0.1-1.25; the §3 decode row now names the 110 tok/s arm as next best instead of skipping it; §2's KV bullet no longer says the 14B only fits 4k; the decision-map sentence placed the quality pick top-left, it is the top-right extreme; Figure 1's caption now names the 1 GiB overhead in the footprint. |
| 1.16 | 10th November 2026 | §4 now says which uncertainty it quotes: the three figures there are one standard error, the paragraph defines the 95% confidence intervals the charts draw and says they are about double these. §11's memory figures move to the host's own units — 128 GiB and a 100 GiB GTT window — replacing a 96 GiB figure that no reading on the box produces. |
| 1.15 | 10th November 2026 | Corrects the claim that power and temperature were not recorded: the host's monitor logs both at ~2 s throughout, and the platform table now says so with retention. The introduction quotes the campaign's measured envelope — GPU 69 °C mean, 88 °C hottest sample, package power 96 W mean, 129 W peak — so the throughput numbers come with a thermal context instead of an unstated one. |
| 1.14 | 10th November 2026 | The platform table gains the OS: distribution, init, C library, and on the kernel row the pstate mode and EPP hint, because on this host the governor is what decides how long the boost is held. |
| 1.13 | 10th November 2026 | The platform table gains storage: the NVMe drive and filesystem the weight files live on, with measured direct-read rates. It is in the table to say what it does not affect — weights are read once at load, so storage sets load time, not decode. |
| 1.12 | 10th November 2026 | The introduction gains a platform table: CPU, GPU, unified memory and the GTT window, kernel, graphics stack, inference build and server flags, each with the reason it is stated. Power and temperature are named as unrecorded rather than implied to be controlled. The spec list that used to sit in the prose is folded into the table instead of being repeated above it. It is Table 1, so every later table is numbered one higher than before. |
| 1.11 | 10th November 2026 | Mean quality and quality per GiB now appear in every table that lists per-model scores: two columns in the roster (§1) and two rows in the controlled pair (§7). Both are marked derived, and both state the divisor is the footprint at the model's context. The ladder (§8) says why it has no per-GiB column. |
| 1.10 | 10th November 2026 | Fixes "both platforms" in §4 and in the transferability table: that phrase dates from when the page compared only this box and a discrete card. It now names the three architectures the page actually compares and gives each one's bandwidth range. |
| 1.9 | 10th November 2026 | Removes duplication in §2: the axis bullets restated the table's 'what it does not tell you' column and the mean-quality row a third time. The bullets now carry only the incentive each axis creates, and the table keeps scope. |
| 1.8 | 10th November 2026 | The axis table gains the two derived metrics the rest of the page ranks on — mean quality and quality per GiB — marked as arithmetic rather than benchmarks, with what each can and cannot tell you. |
| 1.7 | 10th November 2026 | Defines cap, budget, footprint and KV cache in §2 alongside the axes — the four terms every number on the page is qualified by, none of which was explained where it was first used. |
| 1.6 | 10th November 2026 | Adds §2: what HumanEval, MMLU-Pro, IFEval, prefill/decode and the riddle probes actually measure, how each is scored, what was run here, and what each one cannot tell you — before any table of scores. Sections and tables renumbered. |
| 1.5 | 10th November 2026 | Names the author and copyright holder (Dom, github.com/barmynon) instead of leaving the person behind the measurements anonymous, and adds a `CITATION.cff` so the work can be cited. |
| 1.4 | 10th November 2026 | Title now says local LLMs. Adds the licence section: what CC BY 4.0 covers here (expression, figures, compilation and the sui generis database right), what it cannot cover (the facts, the weights, the benchmarks), and the attribution line. |
| 1.3 | 10th November 2026 | Adds a decision map (Figure 6): mean quality against footprint with the 15 GiB wall, a stated 0.78 competitive line and the three picks ringed, so "where is good" is visible without reading a table. Deliberately not a quadrant — no median crosshair, because the good direction here is up and to the left. Figures renumbered; the decode figure now marks the region that fits the card. |
| 1.2 | 10th November 2026 | the card comparison extended to thirteen cards across four vendors: five AMD boards added (RX 7600 XT, 9060 XT, 6800, 6950 XT, 7900 GRE), so the class can be compared within and across vendors, and the reference machine named as the Minisforum MS-S1 MAX instead of "this box". |
| 1.1 | 10th November 2026 | Adds the 16 GB card section: the 16 GB cards actually on the market, their vendor bandwidth, and the decode range each implies for the roster's two reference models. Predicted, not measured — the method and its calibration are stated with it. |
| 1.0 | 10th November 2026 | First release. Eleven files measured for the 16 GiB class on a host with no VRAM ceiling, three axes at stated caps, fit and KV arithmetic from the same roster file the runs used, six computed figures, the three-platform bandwidth comparison. |

*The version number belongs to this page. The wider report on this platform has its own history in
[the change log](changelog.html); a correction to a number here bumps the version above and states what the
previous value was, on the same rule the main report follows.*


---

*Source, data and build scripts: [github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io](https://github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io). Text, figures and data: CC BY 4.0.*
