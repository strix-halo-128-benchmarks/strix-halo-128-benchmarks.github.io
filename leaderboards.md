# Leaderboards, by axis

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

35 measured rows: **16 servable**, 19 retired but kept in place, because a
leaderboard with the failures deleted is how the same 60 GB gets downloaded twice.

---

## Code — HumanEval, 164 items

| # | model | HumanEval | n | cap | build | measured | status |
|---:|---|---:|---:|---:|---|---|---|
| 1 | gemma4-31b | 0.9634 | 164 | 2048 | fork pre-identity | 2026-10-21 | ✗ retired |
| 2 | minicpm-v47-35b | 0.9573 | 164 | 4096 | bolt pre-identity | 2026-10-18 | ✓ |
| 3 | gemma4-26b-uncen | 0.9573 | 164 | 2048 | fork b3-1a33095 | 2026-10-28 | ✓ driver |
| 4 | gemma4-26b-a4b | 0.9573 | 164 | 2048 | fork b3-1a33095 | 2026-10-30 | ✗ retired |
| 5 | ornith-122b | 0.9512 | 164 | 4096 | fork pre-identity | 2026-10-20 | ✓ |
| 6 | nemotron-super-120b | 0.9512 | 164 | 4096 | bolt pre-identity | 2026-10-18 | ✗ retired |
| 7 | gemma4-26b-qat-q4 | 0.9512 | 164 | 2048 | fork pre-identity | 2026-10-21 | ✓ |
| 8 | Nemotron-Bolt-74B-A9B | 0.9451 | 164 | 2048 | bolt pre-identity | 2026-10-16 | ✗ retired |
| 9 | gptoss-abliterated | 0.9268 | 164 | 2048 | fork pre-identity | 2026-10-13 | ✓ |
| 10 | ornith-mtp-21g | 0.9207 | 164 | 4096 | fork pre-identity | 2026-10-17 | ✓ |
| 11 | flint (i1-Q4_K_M) | 0.9167 | 60 | 4096 | flint pre-identity | 2026-10-25 | ✗ retired |
| 12 | Swift-1.5-FN-Heretic | 0.9167 | 60 | 2048 | fork b3-1a33095 | 2026-11-05 | ✓ |
| 13 | mellum21-fork | 0.9146 (above standard cap) | 164 | 8192 | fork pre-identity | 2026-10-18 | ✗ retired |
| 14 | qwen3next-q4 | 0.9146 | 164 | 2048 | fork b3-1a33095 | 2026-10-31 | ✓ |
| 15 | Groot-65B-A6B | 0.9000 | 60 | 2048 | bolt b1-a30fb49 | 2026-11-05 | ✗ retired |
| 16 | mellum | 0.8780 | 164 | 4096 | fork pre-identity | 2026-10-12 | ✗ retired |
| 17 | qwen38-35b | 0.8720 | 164 | 4096 | fork b3-1a33095 | 2026-11-01 | ✓ |
| 18 | Clover-35B-A3B-Preview | 0.8598 | 164 | 4096 | clover b1-6b9c0cf | 2026-11-03 | ✗ retired |
| 19 | lfm25-24b-a2b | 0.8537 | 164 | 4096 | fork pre-identity | 2026-10-17 | ✓ |
| 20 | Axion-1.0-35B | 0.8500 | 60 | 2048 | fork b3-1a33095 | 2026-11-05 | ✓ |
| 21 | qwen38fn-abl | 0.8476 | 164 | 2048 | fork pre-identity | 2026-10-13 | ✓ |
| 22 | Ornith-1.5-35B | 0.8354 | 164 | 4096 | fork b3-1a33095 | 2026-11-01 | ✓ |
| 23 | Kimi-Linear-48B-A3B-abl | 0.7866 (above standard cap) | 164 | 8192 | fork b3-1a33095 | 2026-11-01 | ✗ retired |
| 24 | kimi | 0.7866 | 164 | 2048 | fork pre-identity | 2026-10-14 | ✗ retired |
| 25 | hy-memory-30b-a3b | 0.7805 | 164 | 2048 | fork pre-identity | 2026-10-17 | ✗ retired |
| 26 | graft-50b-a3b | 0.7805 | 164 | 2048 | fork pre-identity | 2026-10-19 | ✗ retired |
| 27 | hy-memory-30b-a3b-q8 | 0.7683 | 164 | 2048 | fork pre-identity | 2026-10-17 | ✗ retired |
| 28 | ornith35b (uncensored) | 0.5671 | 164 | 4096 | fork b3-1a33095 | 2026-10-31 | ✓ boot |

The driver is `gemma4-26b-uncen` — 15.6 GiB, 56.9 t/s, and still the best coder on the box. The three
largest models here (122B, 120B) sit below it on code while running 2-2.5× slower: size buys knowledge
fidelity on this platform, not code.

## Knowledge — MMLU-Pro, 120 items, chat 0-shot

| # | model | MMLU-Pro | n | cap | build | measured | status |
|---:|---|---:|---:|---:|---|---|---|
| 1 | qwen38fn-abl | 0.8750 | 40 | 2048 | fork pre-identity | 2026-10-13 | ✓ |
| 2 | gemma4-31b | 0.8667 | 120 | 2048 | fork pre-identity | 2026-10-21 | ✗ retired |
| 3 | gemma4-26b-a4b | 0.8667 | 120 | 2048 | fork b3-1a33095 | 2026-10-30 | ✗ retired |
| 4 | gemma4-26b-uncen | 0.8500 | 120 | 2048 | fork b3-1a33095 | 2026-10-28 | ✓ driver |
| 5 | gemma4-26b-qat-q4 | 0.8417 | 120 | 2048 | fork pre-identity | 2026-10-21 | ✓ |
| 6 | mellum21-fork | 0.8083 (above standard cap) | 120 | 8192 | fork pre-identity | 2026-10-18 | ✗ retired |
| 7 | Swift-1.5-FN-Heretic | 0.8000 | 40 | 2048 | fork b3-1a33095 | 2026-11-05 | ✓ |
| 8 | ornith-122b | 0.7917 | 120 | 4096 | fork pre-identity | 2026-10-20 | ✓ |
| 9 | minicpm-v47-35b | 0.7750 | 120 | 4096 | bolt pre-identity | 2026-10-18 | ✓ |
| 10 | ornith-mtp-21g | 0.7750 | 120 | 2048 | fork pre-identity | 2026-10-17 | ✓ |
| 11 | Axion-1.0-35B | 0.7750 | 40 | 2048 | fork b3-1a33095 | 2026-11-05 | ✓ |
| 12 | nemotron-super-120b | 0.7667 | 120 | 4096 | bolt pre-identity | 2026-10-18 | ✗ retired |
| 13 | Ling-3.0-flash | 0.7667 | 120 | 2048 | fork pre-identity | 2026-10-22 | ✗ retired |
| 14 | gptoss-abliterated | 0.7500 | 120 | 2048 | fork pre-identity | 2026-10-13 | ✓ |
| 15 | Groot-65B-A6B | 0.7500 | 40 | 2048 | bolt b1-a30fb49 | 2026-11-05 | ✗ retired |
| 16 | hy-memory-30b-a3b-q8 | 0.7500 | 120 | 2048 | fork pre-identity | 2026-10-17 | ✗ retired |
| 17 | qwen3next-q4 | 0.7417 | 120 | 2048 | fork b3-1a33095 | 2026-10-31 | ✓ |
| 18 | hy-memory-30b-a3b | 0.7250 | 120 | 2048 | fork pre-identity | 2026-10-17 | ✗ retired |
| 19 | mellum | 0.7000 | 120 | 4096 | fork pre-identity | 2026-10-12 | ✗ retired |
| 20 | lfm25-24b-a2b | 0.6917 | 120 | 4096 | fork pre-identity | 2026-10-17 | ✓ |
| 21 | graft-50b-a3b | 0.6583 | 120 | 2048 | fork pre-identity | 2026-10-19 | ✗ retired |
| 22 | qwen38-35b | 0.6417 | 120 | 4096 | fork b3-1a33095 | 2026-11-01 | ✓ |
| 23 | ornith35b (uncensored) | 0.6333 | 120 | 4096 | fork b3-1a33095 | 2026-10-31 | ✓ boot |
| 24 | Kimi-Linear-48B-A3B-abl | 0.5833 (above standard cap) | 120 | 8192 | fork b3-1a33095 | 2026-11-01 | ✗ retired |
| 25 | kimi | 0.5500 | 120 | 2048 | fork pre-identity | 2026-10-14 | ✗ retired |
| 26 | Ornith-1.5-35B | 0.4417 | 120 | 4096 | fork b3-1a33095 | 2026-11-01 | ✓ |
| 27 | Clover-35B-A3B-Preview | 0.4000 | 120 | 4096 | clover b1-6b9c0cf | 2026-11-03 | ✗ retired |
| 28 | Nemotron-Bolt-74B-A9B | 0.3667 | 120 | 2048 | bolt pre-identity | 2026-10-16 | ✗ retired |

The 26B MoE also leads knowledge. The two 120B-class models recover some ground here and none of it
justifies 60-70 GiB at 23-27 t/s on a box whose best model fits in a sixth of that.

## Reasoning traps — riddles and arithmetic, 14 items

| # | model | riddles | n | cap | build | measured | status |
|---:|---|---:|---:|---:|---|---|---|
| 1 | gemma4-31b | 14/14 | — | — | fork pre-identity | 2026-10-21 | ✗ retired |
| 2 | gemma4-26b-uncen | 14/14 | — | — | fork b3-1a33095 | 2026-10-28 | ✓ driver |
| 3 | gemma4-26b-a4b | 14/14 | — | — | fork b3-1a33095 | 2026-10-30 | ✗ retired |
| 4 | gemma4-26b-qat-q4 | 14/14 | — | — | fork pre-identity | 2026-10-21 | ✓ |
| 5 | qwen3next-q6 | 14/14 | — | — | fork pre-identity | 2026-10-10 | ✓ |
| 6 | qwen3next-q4 | 14/14 | — | — | fork b3-1a33095 | 2026-10-31 | ✓ |
| 7 | qwen38-35b | 14/14 | — | — | fork b3-1a33095 | 2026-11-01 | ✓ |
| 8 | Clover-35B-A3B-Preview | 14/14 | — | — | clover b1-6b9c0cf | 2026-11-03 | ✗ retired |
| 9 | graft-50b-a3b | 14/14 | — | — | fork pre-identity | 2026-10-19 | ✗ retired |
| 10 | Nemotron-Bolt-74B-A9B | 13/14 | — | — | bolt pre-identity | 2026-10-16 | ✗ retired |
| 11 | Kimi-Linear-48B-A3B-abl | 13/14 | — | — | fork b3-1a33095 | 2026-11-01 | ✗ retired |
| 12 | Ornith-1.5-35B | 13/14 | — | — | fork b3-1a33095 | 2026-11-01 | ✓ |
| 13 | kimi | 13/14 | — | — | fork pre-identity | 2026-10-14 | ✗ retired |
| 14 | ornith-122b | 12/14 | — | — | fork pre-identity | 2026-10-20 | ✓ |
| 15 | gptoss | 12/14 | — | — | fork pre-identity | 2026-10-12 | ✓ |
| 16 | qwen35 | 12/14 | — | — | fork pre-identity | 2026-10-11 | ✗ retired |
| 17 | qwen36-35b | 12/14 | — | — | fork pre-identity | 2026-10-12 | ✗ retired |
| 18 | hy-memory-30b-a3b | 12/14 | — | — | fork pre-identity | 2026-10-17 | ✗ retired |
| 19 | ornith35b (uncensored) | 12/14 | — | — | fork b3-1a33095 | 2026-10-31 | ✓ boot |
| 20 | nemotron-super-120b | 11/14 | — | — | bolt pre-identity | 2026-10-18 | ✗ retired |
| 21 | ornith-mtp-21g | 11/14 | — | — | fork pre-identity | 2026-10-17 | ✓ |
| 22 | Swift-1.5-FN-Heretic | 11/14 | — | — | fork b3-1a33095 | 2026-11-05 | ✓ |
| 23 | mellum | 11/14 | — | — | fork pre-identity | 2026-10-12 | ✗ retired |
| 24 | qwen38fn-abl | 11/14 | — | — | fork pre-identity | 2026-10-13 | ✓ |
| 25 | hy-memory-30b-a3b-q8 | 11/14 | — | — | fork pre-identity | 2026-10-17 | ✗ retired |
| 26 | Ling-3.0-flash | 11/14 | — | — | fork pre-identity | 2026-10-22 | ✗ retired |
| 27 | minicpm-v47-35b | 10/14 | — | — | bolt pre-identity | 2026-10-18 | ✓ |
| 28 | gptoss-abliterated | 10/14 | — | — | fork pre-identity | 2026-10-13 | ✓ |
| 29 | flint (i1-Q4_K_M) | 10/14 | — | — | flint pre-identity | 2026-10-25 | ✗ retired |
| 30 | mellum21-fork | 10/14 | — | — | fork pre-identity | 2026-10-18 | ✗ retired |
| 31 | lfm25-24b-a2b | 10/14 | — | — | fork pre-identity | 2026-10-17 | ✓ |
| 32 | Axion-1.0-35B | 10/14 | — | — | fork b3-1a33095 | 2026-11-05 | ✓ |
| 33 | Groot-65B-A6B | 9/14 | — | — | bolt b1-a30fb49 | 2026-11-05 | ✗ retired |
| 34 | nemotron-bolt (broken load) | 8/14 | — | — | fork pre-identity | 2026-10-21 | ✗ retired |

Fourteen hand-written riddles and three arithmetic traps. Not a benchmark in the psychometric sense: it
catches a model that pattern-matches an answer without following the question, which is exactly the
failure the code and knowledge axes do not show. `14/14` is the ceiling; several strong coders score
10-11 because they answer confidently and wrongly.

## Speed — decode tokens/second

| # | model | decode | n | cap | build | measured | status |
|---:|---|---:|---:|---:|---|---|---|
| 1 | mellum21-fork | 111.9 t/s | — | — | fork pre-identity | 2026-10-18 | ✗ retired |
| 2 | lfm25-24b-a2b | 106.6 t/s | — | — | fork pre-identity | 2026-10-17 | ✓ |
| 3 | mellum | 91.8 t/s | — | — | fork pre-identity | 2026-10-12 | ✗ retired |
| 4 | Axion-1.0-35B | 76.2 t/s | — | — | fork b3-1a33095 | 2026-11-05 | ✓ |
| 5 | qwen38-35b | 74.8 t/s | — | — | fork b3-1a33095 | 2026-11-01 | ✓ |
| 6 | Kimi-Linear-48B-A3B-abl | 74.8 t/s | — | — | fork b3-1a33095 | 2026-11-01 | ✗ retired |
| 7 | hy-memory-30b-a3b | 74.7 t/s | — | — | fork pre-identity | 2026-10-17 | ✗ retired |
| 8 | Ornith-1.5-35B | 74.1 t/s | — | — | fork b3-1a33095 | 2026-11-01 | ✓ |
| 9 | Nemotron-Bolt-74B-A9B | 72.8 t/s | — | — | bolt pre-identity | 2026-10-16 | ✗ retired |
| 10 | flint (i1-Q4_K_M) | 71.1 t/s | — | — | flint pre-identity | 2026-10-25 | ✗ retired |
| 11 | ornith35b (uncensored) | 69.9 t/s | — | — | fork b3-1a33095 | 2026-10-31 | ✓ boot |
| 12 | kimi | 67.4 t/s | — | — | fork pre-identity | 2026-10-14 | ✗ retired |
| 13 | ornith-mtp-21g | 65.2 t/s | — | — | fork pre-identity | 2026-10-17 | ✓ |
| 14 | minicpm-v47-35b | 64.6 t/s | — | — | bolt pre-identity | 2026-10-18 | ✓ |
| 15 | gemma4-26b-qat-q4 | 59.5 t/s | — | — | fork pre-identity | 2026-10-21 | ✓ |
| 16 | qwen3next-q4 | 58.1 t/s | — | — | fork b3-1a33095 | 2026-10-31 | ✓ |
| 17 | qwen36-35b | 57.1 t/s | — | — | fork pre-identity | 2026-10-12 | ✗ retired |
| 18 | gemma4-26b-uncen | 56.9 t/s | — | — | fork b3-1a33095 | 2026-10-28 | ✓ driver |
| 19 | graft-50b-a3b | 54.3 t/s | — | — | fork pre-identity | 2026-10-19 | ✗ retired |
| 20 | Clover-35B-A3B-Preview | 53.7 t/s | — | — | clover b1-6b9c0cf | 2026-11-03 | ✗ retired |
| 21 | qwen38fn-abl | 52.9 t/s | — | — | fork pre-identity | 2026-10-13 | ✓ |
| 22 | hy-memory-30b-a3b-q8 | 52.3 t/s | — | — | fork pre-identity | 2026-10-17 | ✗ retired |
| 23 | gptoss-abliterated | 50.5 t/s | — | — | fork pre-identity | 2026-10-13 | ✓ |
| 24 | gptoss | 50.1 t/s | — | — | fork pre-identity | 2026-10-12 | ✓ |
| 25 | gemma4-26b-a4b | 49.4 t/s | — | — | fork b3-1a33095 | 2026-10-30 | ✗ retired |
| 26 | qwen3next-q6 | 45.8 t/s | — | — | fork pre-identity | 2026-10-10 | ✓ |
| 27 | Ling-3.0-flash | 43.5 t/s | — | — | fork pre-identity | 2026-10-22 | ✗ retired |
| 28 | Groot-65B-A6B | 27.6 t/s | — | — | bolt b1-a30fb49 | 2026-11-05 | ✗ retired |
| 29 | nemotron-super-120b | 27.1 t/s | — | — | bolt pre-identity | 2026-10-18 | ✗ retired |
| 30 | Swift-1.5-FN-Heretic | 25.6 t/s | — | — | fork b3-1a33095 | 2026-11-05 | ✓ |
| 31 | ornith-122b | 23.3 t/s | — | — | fork pre-identity | 2026-10-20 | ✓ |
| 32 | qwen35 | 22.9 t/s | — | — | fork pre-identity | 2026-10-11 | ✗ retired |
| 33 | nemotron-bolt (broken load) | 22.7 t/s | — | — | fork pre-identity | 2026-10-21 | ✗ retired |
| 34 | qwen38fn32-prune2 | 20.0 t/s | — | — | qwen4exp-var b1-1844325 | 2026-11-03 | ✗ retired |
| 35 | gemma4-31b | 17.0 t/s | — | — | fork pre-identity | 2026-10-21 | ✗ retired |

Decode is bandwidth-bound on this platform (~256 GB/s shared with the CPU), so it tracks active
parameters, not total parameters. The top of this table is two ~12-24B MoEs; the bottom is a 120B.

## Prefill — prompt tokens/second

| # | model | prefill | n | cap | build | measured | status |
|---:|---|---:|---:|---:|---|---|---|
| 1 | lfm25-24b-a2b | 2930 t/s | — | — | fork pre-identity | 2026-10-17 | ✓ |
| 2 | mellum21-fork | 2723 t/s | — | — | fork pre-identity | 2026-10-18 | ✗ retired |
| 3 | mellum | 2442 t/s | — | — | fork pre-identity | 2026-10-12 | ✗ retired |
| 4 | gemma4-26b-qat-q4 | 1900 t/s | — | — | fork pre-identity | 2026-10-21 | ✓ |
| 5 | Kimi-Linear-48B-A3B-abl | 1774 t/s | — | — | fork b3-1a33095 | 2026-11-01 | ✗ retired |
| 6 | ornith35b (uncensored) | 1762 t/s | — | — | fork b3-1a33095 | 2026-10-31 | ✓ boot |
| 7 | gemma4-26b-uncen | 1759 t/s | — | — | fork b3-1a33095 | 2026-10-28 | ✓ driver |
| 8 | Ornith-1.5-35B | 1633 t/s | — | — | fork b3-1a33095 | 2026-11-01 | ✓ |
| 9 | ornith-mtp-21g | 1610 t/s | — | — | fork pre-identity | 2026-10-17 | ✓ |
| 10 | minicpm-v47-35b | 1600 t/s | — | — | bolt pre-identity | 2026-10-18 | ✓ |
| 11 | kimi | 1597 t/s | — | — | fork pre-identity | 2026-10-14 | ✗ retired |
| 12 | qwen38-35b | 1550 t/s | — | — | fork b3-1a33095 | 2026-11-01 | ✓ |
| 13 | qwen36-35b | 1548 t/s | — | — | fork pre-identity | 2026-10-12 | ✗ retired |
| 14 | hy-memory-30b-a3b | 1515 t/s | — | — | fork pre-identity | 2026-10-17 | ✗ retired |
| 15 | Clover-35B-A3B-Preview | 1461 t/s | — | — | clover b1-6b9c0cf | 2026-11-03 | ✗ retired |
| 16 | hy-memory-30b-a3b-q8 | 1459 t/s | — | — | fork pre-identity | 2026-10-17 | ✗ retired |
| 17 | Axion-1.0-35B | 1422 t/s | — | — | fork b3-1a33095 | 2026-11-05 | ✓ |
| 18 | graft-50b-a3b | 1368 t/s | — | — | fork pre-identity | 2026-10-19 | ✗ retired |
| 19 | qwen3next-q4 | 1219 t/s | — | — | fork b3-1a33095 | 2026-10-31 | ✓ |
| 20 | qwen3next-q6 | 1189 t/s | — | — | fork pre-identity | 2026-10-10 | ✓ |
| 21 | gptoss-abliterated | 1052 t/s | — | — | fork pre-identity | 2026-10-13 | ✓ |
| 22 | gptoss | 1045 t/s | — | — | fork pre-identity | 2026-10-12 | ✓ |
| 23 | qwen35 | 622 t/s | — | — | fork pre-identity | 2026-10-11 | ✗ retired |
| 24 | ornith-122b | 605 t/s | — | — | fork pre-identity | 2026-10-20 | ✓ |
| 25 | Groot-65B-A6B | 597 t/s | — | — | bolt b1-a30fb49 | 2026-11-05 | ✗ retired |
| 26 | nemotron-bolt (broken load) | 586 t/s | — | — | fork pre-identity | 2026-10-21 | ✗ retired |
| 27 | Nemotron-Bolt-74B-A9B | 577 t/s | — | — | bolt pre-identity | 2026-10-16 | ✗ retired |
| 28 | Swift-1.5-FN-Heretic | 512 t/s | — | — | fork b3-1a33095 | 2026-11-05 | ✓ |
| 29 | qwen38fn-abl | 448 t/s | — | — | fork pre-identity | 2026-10-13 | ✓ |
| 30 | nemotron-super-120b | 411 t/s | — | — | bolt pre-identity | 2026-10-18 | ✗ retired |
| 31 | qwen38fn32-prune2 | 397 t/s | — | — | qwen4exp-var b1-1844325 | 2026-11-03 | ✗ retired |
| 32 | gemma4-31b | 350 t/s | — | — | fork pre-identity | 2026-10-21 | ✗ retired |

Prefill is shader-bound and moves far more between builds than decode does. Use it to size long-prompt
work, not to rank models generally.

---

## Floors — HumanEval measured below the 2048-token standard

| # | model | HumanEval | n | cap | build | measured | status |
|---:|---|---:|---:|---:|---|---|---|
| 1 | nemotron-bolt (broken load) | 0.1786 **floor** | 56 | 512 | fork pre-identity | 2026-10-21 | ✗ retired |

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
