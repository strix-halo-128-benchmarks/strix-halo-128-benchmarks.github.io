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

53 measured rows: **34 servable**, 19 retired but kept in place, because a
leaderboard with the failures deleted is how the same 60 GB gets downloaded twice.

---

## Code — HumanEval, 164 items

| # | model | HumanEval | n | cap | build | measured | status |
|---:|---|---:|---:|---:|---|---|---|
| 1 | lfm25-24b-a2b (thinking) | 0.9695 (above standard cap) | 164 | 8192 | fork b3-1a33095 | 2026-11-10 | ✓ |
| 2 | air-26b-a4b | 0.9695 | 164 | 2048 | fork b11581-19b458b | 2026-11-24 | ✓ |
| 3 | gemma4-31b | 0.9634 | 164 | 2048 | fork pre-identity | 2026-10-21 | ✗ retired |
| 4 | minicpm-v47-35b | 0.9573 | 164 | 4096 | bolt pre-identity | 2026-10-18 | ✓ |
| 5 | gemma4-26b-uncen | 0.9573 | 164 | 2048 | fork b3-1a33095 | 2026-10-28 | ✓ driver |
| 6 | gemma4-26b-a4b | 0.9573 | 164 | 2048 | fork b3-1a33095 | 2026-10-30 | ✗ retired |
| 7 | ornith-122b | 0.9512 | 164 | 4096 | fork pre-identity | 2026-10-20 | ✓ |
| 8 | nemotron-super-120b | 0.9512 | 164 | 4096 | bolt pre-identity | 2026-10-18 | ✗ retired |
| 9 | gemma4-26b-qat-q4 | 0.9512 | 164 | 2048 | fork pre-identity | 2026-10-21 | ✓ |
| 10 | Clover-35B-A3B-Preview (IQ2_M, AR mode) | 0.9451 (above standard cap) | 164 | 8192 | fork b11581-19b458b | 2026-11-12 | ✓ |
| 11 | mellum21-fork | 0.9451 (above standard cap) | 164 | 8192 | fork b11581-1a33095 | 2026-11-20 | ✓ |
| 12 | Nemotron-Bolt-74B-A9B | 0.9451 | 164 | 2048 | bolt pre-identity | 2026-10-16 | ✗ retired |
| 13 | Groot-19B-A3B | 0.9390 | 164 | 4096 | fork b3-1a33095 | 2026-11-11 | ✓ |
| 14 | Axion-1.0-35B (IQ3_XXS) | 0.9329 (above standard cap) | 164 | 8192 | fork b3-1a33095 | 2026-11-12 | ✓ |
| 15 | gptoss-abliterated | 0.9268 | 164 | 2048 | fork pre-identity | 2026-10-13 | ✓ |
| 16 | ornith-mtp-21g | 0.9207 | 164 | 4096 | fork pre-identity | 2026-10-17 | ✓ |
| 17 | flint (i1-Q4_K_M) | 0.9167 | 60 | 4096 | flint pre-identity | 2026-10-25 | ✗ retired |
| 18 | Swift-1.5-FN-Heretic | 0.9167 | 60 | 2048 | fork b3-1a33095 | 2026-11-05 | ✓ |
| 19 | qwen3next-q4 | 0.9146 | 164 | 2048 | fork b3-1a33095 | 2026-10-31 | ✓ |
| 20 | Ornith-1.5-35B | 0.9024 | 164 | 4096 | fork b11581-19b458b | 2026-11-18 | ✓ |
| 21 | Groot-65B-A6B | 0.9000 | 60 | 2048 | bolt b1-a30fb49 | 2026-11-05 | ✗ retired |
| 22 | lfm25-24b-a2b-htc (thinking) | 0.8902 | 164 | 4096 | fork b11581-1a33095 | 2026-11-16 | ✓ |
| 23 | mellum | 0.8780 | 164 | 4096 | fork pre-identity | 2026-10-12 | ✗ retired |
| 24 | qwen38-35b | 0.8720 | 164 | 4096 | fork b3-1a33095 | 2026-11-01 | ✓ |
| 25 | Laguna-XS-2.1 | 0.8667 | 60 | 4096 | fork b3-1a33095 | 2026-11-06 | ✓ |
| 26 | Clover-35B-A3B-Preview | 0.8598 | 164 | 4096 | clover b1-6b9c0cf | 2026-11-03 | ✗ retired |
| 27 | lfm25-24b-a2b | 0.8537 | 164 | 4096 | fork pre-identity | 2026-10-17 | ✓ |
| 28 | Axion-1.0-35B | 0.8500 | 60 | 2048 | fork b3-1a33095 | 2026-11-05 | ✓ |
| 29 | qwen38fn-abl | 0.8476 | 164 | 2048 | fork pre-identity | 2026-10-13 | ✓ |
| 30 | Lite-Beam-M2.7-229B | 0.8000 | 60 | 4096 | fork b3-1a33095 | 2026-11-08 | ✓ |
| 31 | Kimi-Linear-48B-A3B-abl | 0.7866 (above standard cap) | 164 | 8192 | fork b3-1a33095 | 2026-11-01 | ✗ retired |
| 32 | kimi | 0.7866 | 164 | 2048 | fork pre-identity | 2026-10-14 | ✗ retired |
| 33 | hy-memory-30b-a3b | 0.7805 | 164 | 2048 | fork pre-identity | 2026-10-17 | ✗ retired |
| 34 | graft-50b-a3b | 0.7805 | 164 | 2048 | fork pre-identity | 2026-10-19 | ✗ retired |
| 35 | hy-memory-30b-a3b-q8 | 0.7683 | 164 | 2048 | fork pre-identity | 2026-10-17 | ✗ retired |
| 36 | lfm25-24b-a2b-htc | 0.6890 | 164 | 4096 | fork b11581-1a33095 | 2026-11-16 | ✓ |
| 37 | ornith35b (uncensored) | 0.5671 | 164 | 4096 | fork b3-1a33095 | 2026-10-31 | ✓ boot |

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
| 5 | Clover-35B-A3B-Preview (IQ2_M, AR mode) | 0.8417 (above standard cap) | 120 | 8192 | fork b11581-19b458b | 2026-11-12 | ✓ |
| 6 | gemma4-26b-qat-q4 | 0.8417 | 120 | 2048 | fork pre-identity | 2026-10-21 | ✓ |
| 7 | air-26b-a4b | 0.8333 | 120 | 2048 | fork b11581-19b458b | 2026-11-24 | ✓ |
| 8 | mellum21-fork | 0.8083 (above standard cap) | 120 | 8192 | fork b11581-1a33095 | 2026-11-20 | ✓ |
| 9 | Swift-1.5-FN-Heretic | 0.8000 | 40 | 2048 | fork b3-1a33095 | 2026-11-05 | ✓ |
| 10 | ornith-122b | 0.7917 | 120 | 4096 | fork pre-identity | 2026-10-20 | ✓ |
| 11 | minicpm-v47-35b | 0.7750 | 120 | 4096 | bolt pre-identity | 2026-10-18 | ✓ |
| 12 | ornith-mtp-21g | 0.7750 | 120 | 2048 | fork pre-identity | 2026-10-17 | ✓ |
| 13 | Axion-1.0-35B | 0.7750 | 40 | 2048 | fork b3-1a33095 | 2026-11-05 | ✓ |
| 14 | nemotron-super-120b | 0.7667 | 120 | 4096 | bolt pre-identity | 2026-10-18 | ✗ retired |
| 15 | Ling-3.0-flash | 0.7667 | 120 | 2048 | fork pre-identity | 2026-10-22 | ✗ retired |
| 16 | Axion-1.0-35B (IQ3_XXS) | 0.7583 | 120 | 4096 | fork b3-1a33095 | 2026-11-12 | ✓ |
| 17 | gptoss-abliterated | 0.7500 | 120 | 2048 | fork pre-identity | 2026-10-13 | ✓ |
| 18 | Groot-65B-A6B | 0.7500 | 40 | 2048 | bolt b1-a30fb49 | 2026-11-05 | ✗ retired |
| 19 | hy-memory-30b-a3b-q8 | 0.7500 | 120 | 2048 | fork pre-identity | 2026-10-17 | ✗ retired |
| 20 | qwen3next-q4 | 0.7417 | 120 | 2048 | fork b3-1a33095 | 2026-10-31 | ✓ |
| 21 | hy-memory-30b-a3b | 0.7250 | 120 | 2048 | fork pre-identity | 2026-10-17 | ✗ retired |
| 22 | Groot-19B-A3B | 0.7167 | 120 | 4096 | fork b3-1a33095 | 2026-11-11 | ✓ |
| 23 | Laguna-XS-2.1 | 0.7000 (above standard cap) | 40 | 8192 | fork b3-1a33095 | 2026-11-06 | ✓ |
| 24 | mellum | 0.7000 | 120 | 4096 | fork pre-identity | 2026-10-12 | ✗ retired |
| 25 | lfm25-24b-a2b (thinking) | 0.6917 | 120 | 4096 | fork b3-1a33095 | 2026-11-10 | ✓ |
| 26 | lfm25-24b-a2b | 0.6917 | 120 | 4096 | fork pre-identity | 2026-10-17 | ✓ |
| 27 | Lite-Beam-M2.7-229B | 0.6750 | 40 | 4096 | fork b3-1a33095 | 2026-11-08 | ✓ |
| 28 | graft-50b-a3b | 0.6583 | 120 | 2048 | fork pre-identity | 2026-10-19 | ✗ retired |
| 29 | qwen38-35b | 0.6417 | 120 | 4096 | fork b3-1a33095 | 2026-11-01 | ✓ |
| 30 | ornith35b (uncensored) | 0.6333 | 120 | 4096 | fork b3-1a33095 | 2026-10-31 | ✓ boot |
| 31 | lfm25-24b-a2b-htc (thinking) | 0.6167 | 120 | 4096 | fork b11581-1a33095 | 2026-11-16 | ✓ |
| 32 | Kimi-Linear-48B-A3B-abl | 0.5833 (above standard cap) | 120 | 8192 | fork b3-1a33095 | 2026-11-01 | ✗ retired |
| 33 | kimi | 0.5500 | 120 | 2048 | fork pre-identity | 2026-10-14 | ✗ retired |
| 34 | Ornith-1.5-35B | 0.4250 | 120 | 4096 | fork b11581-19b458b | 2026-11-18 | ✓ |
| 35 | Clover-35B-A3B-Preview | 0.4000 | 120 | 4096 | clover b1-6b9c0cf | 2026-11-03 | ✗ retired |
| 36 | Nemotron-Bolt-74B-A9B | 0.3667 | 120 | 2048 | bolt pre-identity | 2026-10-16 | ✗ retired |
| 37 | lfm25-24b-a2b-htc | 0.2667 | 120 | 4096 | fork b11581-1a33095 | 2026-11-16 | ✓ |

The 26B MoE also leads knowledge. The two 120B-class models recover some ground here and none of it
justifies 60-70 GiB at 23-27 t/s on a box whose best model fits in a sixth of that.

## Reasoning traps — riddles and arithmetic, 14 items

| # | model | riddles | n | cap | build | measured | status |
|---:|---|---:|---:|---:|---|---|---|
| 1 | lfm25-24b-a2b (thinking) | 14/14 | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 2 | air-26b-a4b | 14/14 | — | — | fork b11581-19b458b | 2026-11-24 | ✓ |
| 3 | gemma4-31b | 14/14 | — | — | fork pre-identity | 2026-10-21 | ✗ retired |
| 4 | gemma4-26b-uncen | 14/14 | — | — | fork b3-1a33095 | 2026-10-28 | ✓ driver |
| 5 | gemma4-26b-a4b | 14/14 | — | — | fork b3-1a33095 | 2026-10-30 | ✗ retired |
| 6 | gemma4-26b-qat-q4 | 14/14 | — | — | fork pre-identity | 2026-10-21 | ✓ |
| 7 | Clover-35B-A3B-Preview (IQ2_M, AR mode) | 14/14 | — | — | fork b11581-19b458b | 2026-11-12 | ✓ |
| 8 | Axion-1.0-35B (IQ3_XXS) | 14/14 | — | — | fork b3-1a33095 | 2026-11-12 | ✓ |
| 9 | qwen3next-q6 | 14/14 | — | — | fork pre-identity | 2026-10-10 | ✓ |
| 10 | Hy4-flash (IQ2_S/IQ2_XXS) | 14/14 | — | — | hy4flash-pr b1-f8d4cc4 | 2026-11-19 | ✗ retired |
| 11 | qwen3next-q4 | 14/14 | — | — | fork b3-1a33095 | 2026-10-31 | ✓ |
| 12 | Ornith-1.5-35B | 14/14 | — | — | fork b11581-19b458b | 2026-11-18 | ✓ |
| 13 | gemma-4-12B-QAT | 14/14 | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 14 | lfm25-24b-a2b-htc (thinking) | 14/14 | — | — | fork b11581-1a33095 | 2026-11-16 | ✓ |
| 15 | qwen38-35b | 14/14 | — | — | fork b3-1a33095 | 2026-11-01 | ✓ |
| 16 | gemma-4-E4B-QAT | 14/14 | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 17 | Clover-35B-A3B-Preview | 14/14 | — | — | clover b1-6b9c0cf | 2026-11-03 | ✗ retired |
| 18 | qwen3-14b | 14/14 | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 19 | qwen3-30b-a3b | 14/14 | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 20 | graft-50b-a3b | 14/14 | — | — | fork pre-identity | 2026-10-19 | ✗ retired |
| 21 | gpt-oss-20b-mxfp4 | 14/14 | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 22 | gemma-4-26B-A4B-QAT + MTP drafter | 14/14 | — | — | fork b3-1a33095 | 2026-11-09 | ✓ |
| 23 | Nemotron-Bolt-74B-A9B | 13/14 | — | — | bolt pre-identity | 2026-10-16 | ✗ retired |
| 24 | Groot-19B-A3B | 13/14 | — | — | fork b3-1a33095 | 2026-11-11 | ✓ |
| 25 | Kimi-Linear-48B-A3B-abl | 13/14 | — | — | fork b3-1a33095 | 2026-11-01 | ✗ retired |
| 26 | qwen3-8b | 13/14 | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 27 | kimi | 13/14 | — | — | fork pre-identity | 2026-10-14 | ✗ retired |
| 28 | ornith-122b | 12/14 | — | — | fork pre-identity | 2026-10-20 | ✓ |
| 29 | mellum21-fork | 12/14 | — | — | fork b11581-1a33095 | 2026-11-20 | ✓ |
| 30 | gptoss | 12/14 | — | — | fork pre-identity | 2026-10-12 | ✓ |
| 31 | qwen35 | 12/14 | — | — | fork pre-identity | 2026-10-11 | ✗ retired |
| 32 | qwen36-35b | 12/14 | — | — | fork pre-identity | 2026-10-12 | ✗ retired |
| 33 | mistral-small-3.1-24b | 12/14 | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 34 | hy-memory-30b-a3b | 12/14 | — | — | fork pre-identity | 2026-10-17 | ✗ retired |
| 35 | lfm25-24b-a2b-htc | 12/14 | — | — | fork b11581-1a33095 | 2026-11-16 | ✓ |
| 36 | ornith35b (uncensored) | 12/14 | — | — | fork b3-1a33095 | 2026-10-31 | ✓ boot |
| 37 | nemotron-super-120b | 11/14 | — | — | bolt pre-identity | 2026-10-18 | ✗ retired |
| 38 | ornith-mtp-21g | 11/14 | — | — | fork pre-identity | 2026-10-17 | ✓ |
| 39 | Swift-1.5-FN-Heretic | 11/14 | — | — | fork b3-1a33095 | 2026-11-05 | ✓ |
| 40 | mellum | 11/14 | — | — | fork pre-identity | 2026-10-12 | ✗ retired |
| 41 | qwen38fn-abl | 11/14 | — | — | fork pre-identity | 2026-10-13 | ✓ |
| 42 | hy-memory-30b-a3b-q8 | 11/14 | — | — | fork pre-identity | 2026-10-17 | ✗ retired |
| 43 | Ling-3.0-flash | 11/14 | — | — | fork pre-identity | 2026-10-22 | ✗ retired |
| 44 | minicpm-v47-35b | 10/14 | — | — | bolt pre-identity | 2026-10-18 | ✓ |
| 45 | gptoss-abliterated | 10/14 | — | — | fork pre-identity | 2026-10-13 | ✓ |
| 46 | flint (i1-Q4_K_M) | 10/14 | — | — | flint pre-identity | 2026-10-25 | ✗ retired |
| 47 | Laguna-XS-2.1 | 10/14 | — | — | fork b3-1a33095 | 2026-11-06 | ✓ |
| 48 | lfm25-24b-a2b | 10/14 | — | — | fork pre-identity | 2026-10-17 | ✓ |
| 49 | Axion-1.0-35B | 10/14 | — | — | fork b3-1a33095 | 2026-11-05 | ✓ |
| 50 | Lite-Beam-M2.7-229B | 10/14 | — | — | fork b3-1a33095 | 2026-11-08 | ✓ |
| 51 | Groot-65B-A6B | 9/14 | — | — | bolt b1-a30fb49 | 2026-11-05 | ✗ retired |
| 52 | nemotron-bolt (broken load) | 8/14 | — | — | fork pre-identity | 2026-10-21 | ✗ retired |

Fourteen hand-written riddles and three arithmetic traps. Not a benchmark in the psychometric sense: it
catches a model that pattern-matches an answer without following the question, which is exactly the
failure the code and knowledge axes do not show. `14/14` is the ceiling; several strong coders score
10-11 because they answer confidently and wrongly.

## Speed — decode tokens/second

| # | model | decode | n | cap | build | measured | status |
|---:|---|---:|---:|---:|---|---|---|
| 1 | mellum21-fork | 114.0 t/s | — | — | fork b11581-1a33095 | 2026-11-20 | ✓ |
| 2 | lfm25-24b-a2b (thinking) | 111.2 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 3 | lfm25-24b-a2b-htc (thinking) | 109.6 t/s | — | — | fork b11581-1a33095 | 2026-11-16 | ✓ |
| 4 | lfm25-24b-a2b | 106.6 t/s | — | — | fork pre-identity | 2026-10-17 | ✓ |
| 5 | lfm25-24b-a2b-htc | 106.0 t/s | — | — | fork b11581-1a33095 | 2026-11-16 | ✓ |
| 6 | Axion-1.0-35B (IQ3_XXS) | 93.8 t/s | — | — | fork b3-1a33095 | 2026-11-12 | ✓ |
| 7 | mellum | 91.8 t/s | — | — | fork pre-identity | 2026-10-12 | ✗ retired |
| 8 | Laguna-XS-2.1 | 87.7 t/s | — | — | fork b3-1a33095 | 2026-11-06 | ✓ |
| 9 | Ornith-1.5-35B | 80.5 t/s | — | — | fork b11581-19b458b | 2026-11-18 | ✓ |
| 10 | qwen3-30b-a3b | 79.7 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 11 | Axion-1.0-35B | 76.2 t/s | — | — | fork b3-1a33095 | 2026-11-05 | ✓ |
| 12 | qwen38-35b | 74.8 t/s | — | — | fork b3-1a33095 | 2026-11-01 | ✓ |
| 13 | Kimi-Linear-48B-A3B-abl | 74.8 t/s | — | — | fork b3-1a33095 | 2026-11-01 | ✗ retired |
| 14 | hy-memory-30b-a3b | 74.7 t/s | — | — | fork pre-identity | 2026-10-17 | ✗ retired |
| 15 | gpt-oss-20b-mxfp4 | 74.4 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 16 | Nemotron-Bolt-74B-A9B | 72.8 t/s | — | — | bolt pre-identity | 2026-10-16 | ✗ retired |
| 17 | flint (i1-Q4_K_M) | 71.1 t/s | — | — | flint pre-identity | 2026-10-25 | ✗ retired |
| 18 | ornith35b (uncensored) | 69.9 t/s | — | — | fork b3-1a33095 | 2026-10-31 | ✓ boot |
| 19 | Clover-35B-A3B-Preview (IQ2_M, AR mode) | 67.5 t/s | — | — | fork b11581-19b458b | 2026-11-12 | ✓ |
| 20 | kimi | 67.4 t/s | — | — | fork pre-identity | 2026-10-14 | ✗ retired |
| 21 | ornith-mtp-21g | 65.2 t/s | — | — | fork pre-identity | 2026-10-17 | ✓ |
| 22 | Groot-19B-A3B | 64.8 t/s | — | — | fork b3-1a33095 | 2026-11-11 | ✓ |
| 23 | minicpm-v47-35b | 64.6 t/s | — | — | bolt pre-identity | 2026-10-18 | ✓ |
| 24 | gemma4-26b-qat-q4 | 59.5 t/s | — | — | fork pre-identity | 2026-10-21 | ✓ |
| 25 | qwen3next-q4 | 58.1 t/s | — | — | fork b3-1a33095 | 2026-10-31 | ✓ |
| 26 | gemma-4-E4B-QAT | 57.8 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 27 | qwen36-35b | 57.1 t/s | — | — | fork pre-identity | 2026-10-12 | ✗ retired |
| 28 | gemma4-26b-uncen | 56.9 t/s | — | — | fork b3-1a33095 | 2026-10-28 | ✓ driver |
| 29 | gemma-4-26B-A4B-QAT + MTP drafter | 54.9 t/s | — | — | fork b3-1a33095 | 2026-11-09 | ✓ |
| 30 | graft-50b-a3b | 54.3 t/s | — | — | fork pre-identity | 2026-10-19 | ✗ retired |
| 31 | Clover-35B-A3B-Preview | 53.7 t/s | — | — | clover b1-6b9c0cf | 2026-11-03 | ✗ retired |
| 32 | qwen38fn-abl | 52.9 t/s | — | — | fork pre-identity | 2026-10-13 | ✓ |
| 33 | hy-memory-30b-a3b-q8 | 52.3 t/s | — | — | fork pre-identity | 2026-10-17 | ✗ retired |
| 34 | gptoss-abliterated | 50.5 t/s | — | — | fork pre-identity | 2026-10-13 | ✓ |
| 35 | gptoss | 50.1 t/s | — | — | fork pre-identity | 2026-10-12 | ✓ |
| 36 | gemma4-26b-a4b | 49.4 t/s | — | — | fork b3-1a33095 | 2026-10-30 | ✗ retired |
| 37 | air-26b-a4b | 48.0 t/s | — | — | fork b11581-19b458b | 2026-11-24 | ✓ |
| 38 | qwen3next-q6 | 45.8 t/s | — | — | fork pre-identity | 2026-10-10 | ✓ |
| 39 | Ling-3.0-flash | 43.5 t/s | — | — | fork pre-identity | 2026-10-22 | ✗ retired |
| 40 | qwen3-8b | 39.0 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 41 | Lite-Beam-M2.7-229B | 34.1 t/s | — | — | fork b3-1a33095 | 2026-11-08 | ✓ |
| 42 | gemma-4-12B-QAT | 27.8 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 43 | Groot-65B-A6B | 27.6 t/s | — | — | bolt b1-a30fb49 | 2026-11-05 | ✗ retired |
| 44 | nemotron-super-120b | 27.1 t/s | — | — | bolt pre-identity | 2026-10-18 | ✗ retired |
| 45 | Swift-1.5-FN-Heretic | 25.6 t/s | — | — | fork b3-1a33095 | 2026-11-05 | ✓ |
| 46 | qwen3-14b | 23.5 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 47 | ornith-122b | 23.3 t/s | — | — | fork pre-identity | 2026-10-20 | ✓ |
| 48 | qwen35 | 22.9 t/s | — | — | fork pre-identity | 2026-10-11 | ✗ retired |
| 49 | nemotron-bolt (broken load) | 22.7 t/s | — | — | fork pre-identity | 2026-10-21 | ✗ retired |
| 50 | qwen38fn32-prune2 | 20.0 t/s | — | — | qwen4exp-var b1-1844325 | 2026-11-03 | ✗ retired |
| 51 | Hy4-flash (IQ2_S/IQ2_XXS) | 18.9 t/s | — | — | hy4flash-pr b1-f8d4cc4 | 2026-11-19 | ✗ retired |
| 52 | gemma4-31b | 17.0 t/s | — | — | fork pre-identity | 2026-10-21 | ✗ retired |
| 53 | mistral-small-3.1-24b | 14.9 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |

Decode is bandwidth-bound on this platform (~256 GB/s shared with the CPU), so it tracks active
parameters, not total parameters. The top of this table is two ~12-24B MoEs; the bottom is a 120B.

## Prefill — prompt tokens/second

| # | model | prefill | n | cap | build | measured | status |
|---:|---|---:|---:|---:|---|---|---|
| 1 | lfm25-24b-a2b (thinking) | 3360 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 2 | lfm25-24b-a2b-htc (thinking) | 3331 t/s | — | — | fork b11581-1a33095 | 2026-11-16 | ✓ |
| 3 | lfm25-24b-a2b-htc | 3225 t/s | — | — | fork b11581-1a33095 | 2026-11-16 | ✓ |
| 4 | lfm25-24b-a2b | 2930 t/s | — | — | fork pre-identity | 2026-10-17 | ✓ |
| 5 | mellum21-fork | 2723 t/s | — | — | fork b11581-1a33095 | 2026-11-20 | ✓ |
| 6 | mellum | 2442 t/s | — | — | fork pre-identity | 2026-10-12 | ✗ retired |
| 7 | gemma-4-E4B-QAT | 2243 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 8 | Groot-19B-A3B | 2176 t/s | — | — | fork b3-1a33095 | 2026-11-11 | ✓ |
| 9 | gpt-oss-20b-mxfp4 | 2169 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 10 | qwen3-30b-a3b | 1910 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 11 | gemma4-26b-qat-q4 | 1900 t/s | — | — | fork pre-identity | 2026-10-21 | ✓ |
| 12 | gemma-4-26B-A4B-QAT + MTP drafter | 1886 t/s | — | — | fork b3-1a33095 | 2026-11-09 | ✓ |
| 13 | Clover-35B-A3B-Preview (IQ2_M, AR mode) | 1849 t/s | — | — | fork b11581-19b458b | 2026-11-12 | ✓ |
| 14 | Kimi-Linear-48B-A3B-abl | 1774 t/s | — | — | fork b3-1a33095 | 2026-11-01 | ✗ retired |
| 15 | ornith35b (uncensored) | 1762 t/s | — | — | fork b3-1a33095 | 2026-10-31 | ✓ boot |
| 16 | gemma4-26b-uncen | 1759 t/s | — | — | fork b3-1a33095 | 2026-10-28 | ✓ driver |
| 17 | air-26b-a4b | 1746 t/s | — | — | fork b11581-19b458b | 2026-11-24 | ✓ |
| 18 | ornith-mtp-21g | 1610 t/s | — | — | fork pre-identity | 2026-10-17 | ✓ |
| 19 | minicpm-v47-35b | 1600 t/s | — | — | bolt pre-identity | 2026-10-18 | ✓ |
| 20 | kimi | 1597 t/s | — | — | fork pre-identity | 2026-10-14 | ✗ retired |
| 21 | qwen38-35b | 1550 t/s | — | — | fork b3-1a33095 | 2026-11-01 | ✓ |
| 22 | qwen36-35b | 1548 t/s | — | — | fork pre-identity | 2026-10-12 | ✗ retired |
| 23 | Axion-1.0-35B (IQ3_XXS) | 1543 t/s | — | — | fork b3-1a33095 | 2026-11-12 | ✓ |
| 24 | hy-memory-30b-a3b | 1515 t/s | — | — | fork pre-identity | 2026-10-17 | ✗ retired |
| 25 | Ornith-1.5-35B | 1507 t/s | — | — | fork b11581-19b458b | 2026-11-18 | ✓ |
| 26 | Clover-35B-A3B-Preview | 1461 t/s | — | — | clover b1-6b9c0cf | 2026-11-03 | ✗ retired |
| 27 | hy-memory-30b-a3b-q8 | 1459 t/s | — | — | fork pre-identity | 2026-10-17 | ✗ retired |
| 28 | Axion-1.0-35B | 1422 t/s | — | — | fork b3-1a33095 | 2026-11-05 | ✓ |
| 29 | graft-50b-a3b | 1368 t/s | — | — | fork pre-identity | 2026-10-19 | ✗ retired |
| 30 | Laguna-XS-2.1 | 1321 t/s | — | — | fork b3-1a33095 | 2026-11-06 | ✓ |
| 31 | qwen3-8b | 1300 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 32 | qwen3next-q4 | 1219 t/s | — | — | fork b3-1a33095 | 2026-10-31 | ✓ |
| 33 | qwen3next-q6 | 1189 t/s | — | — | fork pre-identity | 2026-10-10 | ✓ |
| 34 | gptoss-abliterated | 1052 t/s | — | — | fork pre-identity | 2026-10-13 | ✓ |
| 35 | gptoss | 1045 t/s | — | — | fork pre-identity | 2026-10-12 | ✓ |
| 36 | gemma-4-12B-QAT | 911 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 37 | qwen3-14b | 743 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 38 | qwen35 | 622 t/s | — | — | fork pre-identity | 2026-10-11 | ✗ retired |
| 39 | ornith-122b | 605 t/s | — | — | fork pre-identity | 2026-10-20 | ✓ |
| 40 | Groot-65B-A6B | 597 t/s | — | — | bolt b1-a30fb49 | 2026-11-05 | ✗ retired |
| 41 | nemotron-bolt (broken load) | 586 t/s | — | — | fork pre-identity | 2026-10-21 | ✗ retired |
| 42 | Nemotron-Bolt-74B-A9B | 577 t/s | — | — | bolt pre-identity | 2026-10-16 | ✗ retired |
| 43 | Swift-1.5-FN-Heretic | 512 t/s | — | — | fork b3-1a33095 | 2026-11-05 | ✓ |
| 44 | mistral-small-3.1-24b | 460 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 45 | qwen38fn-abl | 448 t/s | — | — | fork pre-identity | 2026-10-13 | ✓ |
| 46 | nemotron-super-120b | 411 t/s | — | — | bolt pre-identity | 2026-10-18 | ✗ retired |
| 47 | qwen38fn32-prune2 | 397 t/s | — | — | qwen4exp-var b1-1844325 | 2026-11-03 | ✗ retired |
| 48 | gemma4-31b | 350 t/s | — | — | fork pre-identity | 2026-10-21 | ✗ retired |
| 49 | Hy4-flash (IQ2_S/IQ2_XXS) | 276 t/s | — | — | hy4flash-pr b1-f8d4cc4 | 2026-11-19 | ✗ retired |
| 50 | Lite-Beam-M2.7-229B | 261 t/s | — | — | fork b3-1a33095 | 2026-11-08 | ✓ |

Prefill is shader-bound and moves far more between builds than decode does. Use it to size long-prompt
work, not to rank models generally.

---

## Floors — HumanEval measured below the 2048-token standard

| # | model | HumanEval | n | cap | build | measured | status |
|---:|---|---:|---:|---:|---|---|---|
| 1 | Hy4-flash (IQ2_S/IQ2_XXS) | 0.9207 **floor** | 164 | 512 | hy4flash-pr b1-f8d4cc4 | 2026-11-19 | ✗ retired |
| 2 | gemma-4-12B-QAT | 0.8963 **floor** | 164 | 512 | fork b3-1a33095 | 2026-11-10 | ✓ |
| 3 | gemma-4-E4B-QAT | 0.8659 **floor** | 164 | 512 | fork b3-1a33095 | 2026-11-10 | ✓ |
| 4 | qwen3-14b | 0.8537 **floor** | 164 | 512 | fork b3-1a33095 | 2026-11-10 | ✓ |
| 5 | qwen3-30b-a3b | 0.8537 **floor** | 164 | 512 | fork b3-1a33095 | 2026-11-10 | ✓ |
| 6 | mistral-small-3.1-24b | 0.8232 **floor** | 164 | 512 | fork b3-1a33095 | 2026-11-10 | ✓ |
| 7 | qwen3-8b | 0.7866 **floor** | 164 | 512 | fork b3-1a33095 | 2026-11-10 | ✓ |
| 8 | gpt-oss-20b-mxfp4 | 0.5854 **floor** | 164 | 512 | fork b3-1a33095 | 2026-11-10 | ✓ |
| 9 | nemotron-bolt (broken load) | 0.1786 **floor** | 56 | 512 | fork pre-identity | 2026-10-21 | ✗ retired |

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
