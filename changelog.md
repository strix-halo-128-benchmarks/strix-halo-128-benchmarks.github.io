# Change log — every version, and why it changed

This document's history, kept separate from the report so the report can stay about the measurement. Each
entry states what changed and the numbers that forced the change; a correction is only worth anything if it
records what was wrong before it.

Versions before 1.3 are summarised compactly: they predate the build register (§4.1), the cap discipline
(§7.2) and the provenance manifest (§20.5), and their numbers should be read with those absences in mind.

---

### Version 1.16 (2026-11-01)

**The week's most interesting shape does not load, and the reason is in the file.** Qwen3.8-Flash-Next-32B-A6B
"Prune2" (48.31 GiB, `qwen4exp`, 32B total / 6B active) was fetched to test the one gap in this roster — an
active-parameter count between the driver's 4B and the 120B class's 12B. It fails in both trees:

    check_tensor_dims: 'blk.0.ffn_down_exps.weight' expected 640, 2560, 177, got 640, 2560, 64, 1

The header claims 177 experts, the expert tensors hold 64, and the router still has 177 rows — so no single
`expert_count` satisfies the file. Patching the header to 64 moves the error one tensor along to
`ffn_gate_inp`, which is the proof that the export is internally inconsistent rather than mistagged. Recorded
in the not-runnable reference, deleted with its hash, and noted in the ledger so nobody re-downloads 48 GiB to
rediscover it. A re-export with matching counts would be worth testing on shape alone.

That makes three arrivals measured or rejected today (Dark-Craving, Holo4, this one) and none added: the roster
is 17, at 630 GiB.

### Version 1.15 (2026-11-01)

**Two of the week's most-downloaded releases measured, both dominated; and a rebuild tested and refused.**

| model | HE @4096 | MMLU @4096 | riddles | decode | size | verdict |
|---|---|---|---|---|---|---|
| Dark-Craving-26B-A4B v0.3 Q4_K_M | 0.9390 (154/164) | 0.8167 (98/120) | 14/14 | 47.3 t/s | 16.45 GiB | deleted — dominated by the driver on every axis |
| Holo4-35B-A3B MXFP4 | 0.8598 (141/164) | **0.3250 (39/120)** | 13/14 | 60.5 t/s | 18.43 GiB | deleted — no knowledge retrieval |

Dark-Craving is the driver's exact shape and lands 3 and 4 items behind it — inside sampling error — while
decoding 17 % slower in 0.8 GiB more. Holo4 returns all 120 MMLU items as a bare letter in 0.2 s each; against
a 25 % chance floor for ten options, 32.5 % is a finetune that does not retrieve knowledge when the answer is a
single token, while its generative axes (0.8598 code, 13/14 riddles) stay competent. Both were deleted with
byte counts, sha256s and restore recipes in the ledger.

§4.2 is new: the fork's `origin/HEAD` was 1,041 commits ahead with a Vulkan MoE MUL_MAT_ID fusion and a q8_0
mat-vec fix, so it was built and A/B'd on two weight classes. Decode flat to −2.8 %, quality identical, prefill
noise — **not adopted**, and the matrix stays on one build identity rather than becoming a mixture.

### Version 1.14 (2026-11-01)

**A provenance manifest, and licences stated for the first time.** §20.5 lists every servable artefact with
its upstream repository and the licence the card declares, and records which bytes are provably upstream's:
13 of 17 artefacts verify by sha256 against the repository's LFS object id, re-computed on disk rather than
copied from the fetch log. The four that do not are named rather than filled in — they predate the record,
and their hashes are in `data/provenance.json` so anyone can close the gap in a minute.

That closes the largest hole in a document about reproducibility: it described 30 models' behaviour in
detail while never saying where a single file came from or what licence governed it.

### Version 1.13 (2026-11-01)

**Eight stale facts corrected, notation moved to the front, sampling error tabulated.** The headline count
said "33 models" when the matrix has 30 rows out of 50 measured files; the roster was described as 15 units
and 602 GiB in two places (it is 17 and 630); §18.3 still said "33 model files, 16 remain servable"; and
§9.1's `nemotron-super-120b` paragraph quoted **0.9329**, the number §21's own errata had already replaced
with 0.9512 — the one defect of the kind this report exists to prevent. §12 still retired Kimi-Linear, which
is on disk with a million-token window, and figures 15-16 said 27 models.

`MMLU`, `GTT` and `SE` are now defined in §0 rather than in §8 and the glossary; "the box" is gone in favour
of "this machine"; §18.4 states that the 40-60 h were attended time. §8 gains a sampling-error table, so
"is two items a real difference" has one answer instead of three mentions. Figures carry `<title>`/`<desc>`
taken from their own captions.

### Version 1.12 (2026-11-01)

**A per-axis leaderboard page, generated from this matrix.** `leaderboards.html` ranks the same 30 rows
five ways — HumanEval, MMLU-Pro, reasoning traps, decode, prefill — with cap, item count, build and date
on every line, and a separate table for the one sub-2048 floor so a floor is never ranked against a
ceiling. It is generated by `scripts/leaderboards.py` from the sanitised report, not hand-written, so the
two views cannot disagree; the build gate refuses to publish if either page stops linking the other.

Deliberately absent: a composite index (weighting code against knowledge requires assumptions this report
will not make for the reader) and a per-watt ranking (power is measured in §15 but not paired with
throughput per model, so any such number would be invented).

### Version 1.11 (2026-11-01)

**Two new files triaged at the same cap, one accepted and one rejected.**

| model | HumanEval | MMLU-Pro | riddles | perf | verdict |
|---|---|---|---|---|---|
| Kimi-Linear-48B-A3B-abl i1-Q4_K_M, 27.66 GiB | **0.7866** (129/164) @8192 | **0.5833** (70/120) @8192 | 13/14 | pp 1774 / tg 74.8 | **kept** — 1M native ctx |
| Apex-35B-V1.0 Q4_K_M, 21.23 GiB | **0.4146** (68/164) @4096 | 0.5800 (58/100) @4096, thinking off | 9/14 at both 4096 and 8192 | pp 1992 / tg 61.5 | **rejected and deleted** |

Kimi's row matches the safety-tuned `kimi` retired on 2026-10-29 item for item on code (0.7866), at a
10% higher decode rate, and it is the only million-token model on the roster. Its KV cache must be f16
on both sides (`n_embd_head_v = 72` does not divide a q8_0 block of 32, and mixed types are refused),
which caps the measured window at 65536 beside the driver.

Apex is the more instructive failure. At 4096 five of fourteen riddle items returned `completion_n`
equal to the cap with **empty content**; at 8192, three did. It spends the whole budget thinking and
never emits an answer, so this is not a cap artefact and no larger budget fixes it. 2203 s for 164
HumanEval items — 13.4 s/item at 61 t/s — is the same signature. Recorded in the rejected-candidates
reference and deleted with its sha256, so nobody re-downloads 21 GiB to rediscover it.

**Roster 16 → 17 servable; 630 GiB.** Tables 4, 4b, 5, the four league tables and the §9.1 family
paragraph are updated. The throughput league is now actually sorted by decode, which it had not been.

### Version 1.10 (2026-11-01)

**The last two cap-512 floors were re-measured at cap 4096, and they behave differently on each axis.**
Both models were served from a transient unit on :8086 beside the driver, so no resident model moved
and GTT stayed at 53 of 100 GiB.

| run | model | HumanEval @4096 | was @512 | MMLU-Pro @4096 | was @512 | riddles | perf |
|---|---|---|---:|---|---:|---|---|
| `20261101-034435` | qwen38-35b | **0.8720** (143/164) | 0.8537 (140/164) | **0.6417** (77/120) | 0.5083 (61/120) | 14/14 (was 13/14) | pp 1550 / tg 74.8 |
| `20261101-040537` | Ornith-1.5-35B Q4_K_M | **0.8354** (137/164) | 0.8232 (135/164) | **0.4417** (53/120) | 0.4167 (50/120) | 13/14 | pp 1633 / tg 74.1 |

Both scored 3/3 preflight and passed both needles; wall 1237 s and 661 s. The verdicts differ in the
way that matters: `qwen38-35b` was a **genuine floor** — the 512 cap cost it 16 knowledge items
(+13.3 pp, far outside SE at n=120) while costing only 3 code items — whereas `Ornith-1.5-35B` was
**already honest** (+2 code, +3 knowledge items, both inside noise). §9.1 now carries that as a
principle rather than a footnote: the cap's damage is axis-dependent, so one axis read at 512 cannot
tell you which case you are in.

**Rows updated:** Tables 4 and 4b (both rows, with `measured` 2026-11-01 and `build` `fork b3-1a33095`),
the §9.1 "35B trough" paragraph, §16.4's ablation comparison (it excused the boot file's 0.5671 against
a cap-512 row that no longer exists), Table 5's two family rows, the riddles/throughput/knowledge
league tables, and the open-items paragraph. §16.4 also gains the reason `qwen38fn-abl` stays poisoned:
78.1 GiB cannot sit beside a resident model, and the driver is not stopped for a measurement.

**Publication fault, fixed:** the weekly timer fired at 04:05 GMT while these runs were in flight and
published a row that had only its identity and perf axes written. `scripts/publish.sh` now refuses to
build while a `bench-*` unit is active or any run file is younger than 15 minutes, logging the skip
instead.

### Version 1.9.2 (2026-10-31)

**Storage named, and bounded.** §2.3 records the drives (BIWIN X570 PRO 4 TB for system and models, a
Netac 2 TB spare) and the zram swap device, and states plainly what they do and do not affect: load
time, not decode. Decode is LPDDR5X-bandwidth-bound and prefill is shader-bound, so no figure in this
report depends on the SSD — which is worth saying, because "faster NVMe makes local LLMs faster" is a
common and wrong inference. Paging being compressed RAM rather than disk is called out for the same
reason.

### Version 1.9.1 (2026-10-31)

**The hardware is now named.** The report described "this machine" throughout, because the sanitiser
replaced the hostname; that over-corrected, since the chassis model is public product information and
is the first thing a reader needs to place the numbers. It is now stated as a **Minisforum MS-S1 MAX**
with the DMI values that prove it (`product_family`, `product_name`, `sys_vendor`, board, BIOS, EC) in
the header and §2. The hostname, addresses and paths remain unpublished.

### Version 1.9 (2026-10-31)

**What it cost, stated as a range and labelled an estimate.** §18.3 now leads with the only measured
figure — 118 runs, 47.7 hours of benchmark execution — and drops the stale "33 models, 24 servable,
109 GiB" sentence, which predated this month's retirements. §18.4 adds the effort accounting: 222-318
hours total, of which 40-60 needed a person, and 40-60 to reproduce elsewhere now that the tools are
published. It is the only number in the report that is not traceable to a run, so it says that about
itself in the first line.

### Version 1.8 (2026-10-31)

**Every row now names the build that produced it.** §4.1 has always recorded the commit behind each
flavour, but only at flavour-and-window granularity, and the published catalogue carried nothing finer
than `fork`/`upstream`. Both matrices gain a `build` column (`fork b3-1a33095`, `bolt b1-a30fb49`,
`flint pre-identity` …), and the data export now carries `tree` plus `build_info` per run — the commit,
without the absolute path. 28 of 29 matrix rows and all 16 servable rows resolved; `Ling-3.0-flash`
carries `fork pre-identity` because its row has no HumanEval cell and its run predates stamping.

That closes the difference between a claim and a checkable claim: the document says "build identity per
run", and it is now possible, from the published data, to see which commit sits behind every row.

### Version 1.7 (2026-10-31)

**Prior art, and the context curve that was missing.** Reading two other public datasets — `lhl`'s
llama-bench sweeps and `pepuscz`'s Flash-class results — made two gaps obvious and both are now closed
or named:

- **§23 prior art.** Four sources tabulated with what each answers and what it does not, plus §23.1 on
  the single model measured by both (Qwen3.8-Flash-Next: their 465/42.8 t/s at Q4_XL on Ubuntu vs this
  report's 448/52.9 at IQ3_S on CachyOS — different quant, consistent result). Their 30-item quality
  suite cannot rank models because one item is 3.3 pp; that is the gap 164 HumanEval items fills.
- **§23.2 context curve.** The open item about no 32k needle is closed for the deployed driver: five
  depths from 1.8k to 112.9k prompt tokens, retrieval PASS at every one, prefill 1715 → 670 t/s and
  decode 57.2 → 37.7 t/s. The practical rule is to compact before 64k, not at the window edge.
- **§23.3 cross-validation.** Their published 30-item suite, run unchanged on the deployed driver:
  **30/30** (coding 10/10 executed against their own `gold_test`, GSM8K 10/10, math 10/10) — the same
  score their Qwen3.8-Flash-Next deployment reported. The first pass read 26/30 and all four misses were
  harness defects: a last-number grader that scored "$64 for the 16 glasses" as 16, a LaTeX comparison
  that read −2/3 as different from `-\frac{2}{3}`, a `\boxed{}` regex that truncated `\frac{20}{3}`,
  and a fixture whose `gold_answer` for math_08 says 20 where the correct value is 20/3 — a correction
  the source itself documents.
- **New tooling.** `~/bench/ctxcurve.py` produces the curve against a live server (no reload, no unit
  change), and `~/bench/lucebox30.py` runs the published 30-item suite from `Luce-Org/lucebox` so the
  two datasets can be cross-checked on the same model. Both record per-item evidence, not just verdicts.

### Version 1.6 (2026-10-31)

**Every row now says when it was measured.** Tables 4 and 4b gained a `measured` column — the date of
the best-scoring run for that row, derived by joining each row's HumanEval and MMLU values (with their
caps) against `~/runs/catalogue.json` and taking that run's timestamp. 28 of 28 matrix rows and 16 of
16 servable rows resolved; the one row with no HumanEval cell (`Ling-3.0-flash`) was dated from its
MMLU value alone.

The join is scripted, not typed: two rows scoring identically at the same cap would have been a
coin-flip, so the derivation prefers name overlap and then the most recent run, and it is re-runnable
against the catalogue. What the column does not tell you is the model's release date, only when this
box measured it — the spread runs from 2026-10-10 to 2026-10-31.

### Version 1.5 (2026-10-31)

One re-measurement, on the boot model: `ornith35b` (Ornith-1.5-35B-Uncensored-YMQ-M, IQ3_XXS) had
been measured only at **cap 512**, which the table's own rules call a floor. It was re-run at 4096:

- **Run:** `20261031-175808-ornith-boot-4096`, 850 s, HE 164 + MMLU-Pro 120 at cap 4096, served from
  the already-resident boot unit on :8094 — no extra GTT (30.3 of 100 GiB), driver untouched.
- **Result: HE 0.5671 (93/164), MMLU-Pro 0.6333 (76/120), riddles 12/14, both needles, 3/3
  preflight, pp 1761.8 / tg 69.9 t/s.** The published row was 0.5610 / 0.6000 at cap 512.
- **What it settled:** the cap was not hiding anything — one code item and four knowledge items
  move, both inside the sampling noise at n=164 and n=120. The file is a ~0.57 coder at IQ3_XXS,
  and the row now states that on a proper budget instead of a floor. Riddles went the other way
  (13/14 → 12/14): an arithmetic item returned 9.11 where 9.9 was expected.
- **Rows updated:** Table 4, Table 4b, the §9.1 "35B trough" paragraph (which previously excused
  the score as "an aggressive IQ3_XXS load" without having tested that claim), the family-spread
  section, the riddles and throughput league tables.
- **No cap-512 floor remains on disk:** `qwen38-35b` and `Ornith-1.5-35B` (the Q4_K_M file) were both
  re-measured at cap 4096 on 2026-11-01 — see v1.10 in the change log for the numbers.
- **§16.4 corrected:** it listed the uncensored boot file as "unmeasured, no row, no verdict". It now
  has a row (0.5671 / 0.6333 at cap 4096) and the section states plainly that its low score is the
  IQ3_XXS rung plus the tune, not a measured abliteration cost, because the comparison file is a
  cap-512 Q4_K_M row. The Abliterated-MTPv2-21G-ICE build is NOT unmeasured after all — it is the
  file behind the `ornith-mtp-21g` rows (0.9207 code at 4096, 0.7750 knowledge).

### Version 1.4 (2026-10-31)

One new measurement and no method change: `Qwen3-Next-80B UD-Q4_K_XL` was the only artefact on disk
with no capability row, and it was the last one worth spending compute on when the 2026-10-30 model
sweep turned up nothing fit to download (700 repos, 131 artefacts in the 3–70 GiB band, all either
dense, over-pool, a re-quant, or an arch in neither build tree).

- **Run:** `20261031-023533-qwen3next-q4-coverage`, 1385 s, cap 2048, HE 164 items + MMLU-Pro 120.
  Served on :8082 as a transient unit opposite the driver, 75.1 GiB of the 100 GiB pool, so the
  channel never dropped. Result: **HE 0.9146 (150/164), MMLU-Pro 0.7417 (89/120), 14/14 riddles,
  both needles, 3/3 preflight, pp 1218.7 / tg 58.1 t/s.**
- **What it settled:** the file is dominated. A 15.6 GiB driver scores +4.3 pp code and +10.8 pp
  knowledge at the same decode speed, and an 18.7 GiB gpt-oss-abliterated beats it on both axes too.
  42.9 GiB of weights, 3B active, no measurable advantage over files a third of its size. It is now
  a retire candidate on evidence — held only because the Qwen3-Next pair is on the protected list.
- **Tables updated:** the header roster count (15 → 16 artefacts), Table 4 and Table 4b rows, the
  code / knowledge / riddles league tables, §9.1 (new per-model paragraph), §20.3 and the open-items
  list. `~/runs/catalogue.json` rebuilt to 117 rows from 119 run files.
- **One correction carried:** the previous edition said fifteen artefacts had capability rows "plus
  one without" — the plus-one is now scored, so Table 4b's caption says sixteen and every row has
  both axes.

### Version 1.3 (2026-10-30)

This edition changes facts, not method. Every number still comes from a file in `~/runs/` (120 run
files at the time of writing; `~/runs/catalogue.json` rebuilt 2026-10-29 15:53); nothing here is
re-measured except where said. The only new measurement taken for this edition is the gemma4-26b-a4b
Q8_0 re-run on 2026-10-30.

**The roster moved.** Ten artefacts were retired after the previous edition, in two passes, and the
recipes for all ten are in `~/llama-local/RETIRED-models.md`:

```
  2026-10-29   61.6 GiB   Kimi-Linear-48B-A3B (28.0), Hy-Memory-30B-A3B (17.0),
                          Mellum2.1-12B Q6_K (10.1) and its MXFP4 twin (6.5)
  2026-10-30  245.1 GiB   Ling-3.0-flash Q4_K_M (71.7), Swift Qwen3.8-Flash-Next IQ2_XS (63.5),
                          gemma4-26B-A4B Q8_0 (26.1), Nemotron-Bolt-74B IQ2_XXS (23.1),
                          Flint-40B-A2.5B i1-Q4_K_M (22.5), gemma4-31B QAT Q4_0 (18.0),
                          Huihui Coder390 IQ3_S1 (11.3), Nemotron-Bolt-E4B Q8 (8.9)
```

The models directory is 630 GiB and holds 17 artefacts, every one with a capability row — the last
blank cell (`Qwen3-Next-80B UD-Q4_K_XL`) was filled on 2026-10-31. Fourteen user units remain, one of them enabled
(`llama-gemma4-26b-uncen`, :8100), plus the system boot unit `orient-ornith` (:8094).

**The driver changed.** Since 2026-10-28 the channel is answered by the uncensored QAT Q4_K_M build of
gemma4-26b-a4b on :8100, not the QAT Q4_0 build on :8099. Version 1.2 called :8099 the deployed
driver; that unit is disabled and nothing listens on the port. §0, §6.1, §9.1, §11 and §12 are
corrected accordingly, and the endpoint map in §20.2 now lists only live ports.

**Three rows in Table 4 were wrong, and are fixed:**

1. `qwen3next-q6` was published as 0.9207 (164@2048). No run supports it: its best is **0.9296 over
   142 items**, and 0.9207 is `ornith-mtp-21g`'s figure, copied onto it. Symptom to watch for: two
   unrelated models with a score identical to four decimals.
2. `nemotron-super-120b` was published as 0.9329 (164@4096). Its runs read **0.9512 (156/164)** and
   0.9470 (154/164) at that cap; the printed figure matched neither.
3. `gemma4-26b-a4b` and `gemma4-26b-qat-q4` were listed as two models. They are **one file** measured
   twice (156/164 and 154/164, MMLU 101/120 both). The run alias was shared with the Q8_0 baseline.

**What was deliberately not changed.** §10's family-spread analysis, §13's platform comparison, §14's
hosted comparison, §15's power section, §16's abliteration analysis and §17's DeepSeek deployment
analysis were left alone: none of their inputs moved, and re-cutting them would mix a roster change
into an argument about method. Rows for deleted models are retained throughout, marked `✗` with the
retirement date, because a table that silently drops its losers cannot be audited.

**Figures rebuilt, and four pipeline bugs fixed.** §19's ten figures were regenerated from the
rebuilt catalogue, and doing it accurately turned up three defects that had been silently distorting
them: (a) `charts.py` merged every run under one alias, so the Q8_0 gemma and the QAT file collapsed
into each other and both `ornith35b` files did too — it now canonicalises one name per weight file,
and figure 19's fourth pair is a real Q8_0→QAT comparison instead of a file against itself; (b) it
took the *latest* run per axis rather than the *best*, contradicting §9's stated rule — it now takes
the best, so figures and Table 4 agree; (c) §8's poisoned-MMLU rule was applied by deleting the whole
run rather than the cell, so `qwen38fn-abl`'s good HumanEval row (0.8476) disappeared from every figure
along with its 1/120 MMLU — the filter now blanks the axis and keeps the rest; (d) `runs-catalogue.py`
read the FIRST row of each axis, and
IFEval writes an empty n=0 row before its scored n=30 row, so every IFEval score in the catalogue was
being dropped — fixed, which is why the live driver now appears in figures 18 and 21. Figure 23 also
used to plot the retired flint40b-abl run, whose 1-second samples had aged out of the 72 h raw window
so it could no longer be rebuilt; it now plots the 2026-11-01 Kimi-Linear full suite, the longest run
still inside that window.

**Known open items.** `qwen38fn-abl`'s
MMLU-Pro cell is a poisoned 1/120 rather than a score, and it cannot be re-measured without stopping
the driver (the file is 78.1 GiB, past the pool beside a resident model), which this project does not
do; and the driver's context curve (§23.2) now covers 32k, 64k and 113k prompts — but no *other* model
on disk has been measured beyond an 8k needle since the kernel moved to 7.3.0-5.

---

---

*Back to the [report](index.html) · [deleted models and restore recipes](retired-models.html) · [leaderboards by
axis](leaderboards.html).*

---

*Source, data and build scripts: [github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io](https://github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io).*
