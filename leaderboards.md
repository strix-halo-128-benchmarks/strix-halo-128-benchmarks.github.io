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

48 measured rows: **29 servable**, 19 retired but kept in place, because a
leaderboard with the failures deleted is how the same 60 GB gets downloaded twice.

---

## Code — HumanEval, 164 items

| # | model | HumanEval | n | cap | build | measured | status |
|---:|---|---:|---:|---:|---|---|---|
| 1 | lfm25-24b-a2b (thinking) | 0.9695 (above standard cap) | 164 | 8192 | fork b3-1a33095 | 2026-11-10 | ✓ |
| 2 | gemma4-31b | 0.9634 | 164 | 2048 | fork pre-identity | 2026-10-21 | ✗ retired |
| 3 | minicpm-v47-35b | 0.9573 | 164 | 4096 | bolt pre-identity | 2026-10-18 | ✓ |
| 4 | gemma4-26b-uncen | 0.9573 | 164 | 2048 | fork b3-1a33095 | 2026-10-28 | ✓ driver |
| 5 | gemma4-26b-a4b | 0.9573 | 164 | 2048 | fork b3-1a33095 | 2026-10-30 | ✗ retired |
| 6 | ornith-122b | 0.9512 | 164 | 4096 | fork pre-identity | 2026-10-20 | ✓ |
| 7 | nemotron-super-120b | 0.9512 | 164 | 4096 | bolt pre-identity | 2026-10-18 | ✗ retired |
| 8 | gemma4-26b-qat-q4 | 0.9512 | 164 | 2048 | fork pre-identity | 2026-10-21 | ✓ |
| 9 | Nemotron-Bolt-74B-A9B | 0.9451 | 164 | 2048 | bolt pre-identity | 2026-10-16 | ✗ retired |
| 10 | Groot-19B-A3B | 0.9390 | 164 | 4096 | fork b3-1a33095 | 2026-11-11 | ✓ |
| 11 | Axion-1.0-35B (IQ3_XXS) | 0.9329 (above standard cap) | 164 | 8192 | fork b3-1a33095 | 2026-11-12 | ✓ |
| 12 | gptoss-abliterated | 0.9268 | 164 | 2048 | fork pre-identity | 2026-10-13 | ✓ |
| 13 | ornith-mtp-21g | 0.9207 | 164 | 4096 | fork pre-identity | 2026-10-17 | ✓ |
| 14 | flint (i1-Q4_K_M) | 0.9167 | 60 | 4096 | flint pre-identity | 2026-10-25 | ✗ retired |
| 15 | Swift-1.5-FN-Heretic | 0.9167 | 60 | 2048 | fork b3-1a33095 | 2026-11-05 | ✓ |
| 16 | mellum21-fork | 0.9146 (above standard cap) | 164 | 8192 | fork pre-identity | 2026-10-18 | ✗ retired |
| 17 | qwen3next-q4 | 0.9146 | 164 | 2048 | fork b3-1a33095 | 2026-10-31 | ✓ |
| 18 | Groot-65B-A6B | 0.9000 | 60 | 2048 | bolt b1-a30fb49 | 2026-11-05 | ✗ retired |
| 19 | mellum | 0.8780 | 164 | 4096 | fork pre-identity | 2026-10-12 | ✗ retired |
| 20 | qwen38-35b | 0.8720 | 164 | 4096 | fork b3-1a33095 | 2026-11-01 | ✓ |
| 21 | Laguna-XS-2.1 | 0.8667 | 60 | 4096 | fork b3-1a33095 | 2026-11-06 | ✓ |
| 22 | Clover-35B-A3B-Preview | 0.8598 | 164 | 4096 | clover b1-6b9c0cf | 2026-11-03 | ✗ retired |
| 23 | lfm25-24b-a2b | 0.8537 | 164 | 4096 | fork pre-identity | 2026-10-17 | ✓ |
| 24 | Axion-1.0-35B | 0.8500 | 60 | 2048 | fork b3-1a33095 | 2026-11-05 | ✓ |
| 25 | qwen38fn-abl | 0.8476 | 164 | 2048 | fork pre-identity | 2026-10-13 | ✓ |
| 26 | Ornith-1.5-35B | 0.8354 | 164 | 4096 | fork b3-1a33095 | 2026-11-01 | ✓ |
| 27 | Lite-Beam-M2.7-229B | 0.8000 | 60 | 4096 | fork b3-1a33095 | 2026-11-08 | ✓ |
| 28 | Kimi-Linear-48B-A3B-abl | 0.7866 (above standard cap) | 164 | 8192 | fork b3-1a33095 | 2026-11-01 | ✗ retired |
| 29 | kimi | 0.7866 | 164 | 2048 | fork pre-identity | 2026-10-14 | ✗ retired |
| 30 | hy-memory-30b-a3b | 0.7805 | 164 | 2048 | fork pre-identity | 2026-10-17 | ✗ retired |
| 31 | graft-50b-a3b | 0.7805 | 164 | 2048 | fork pre-identity | 2026-10-19 | ✗ retired |
| 32 | hy-memory-30b-a3b-q8 | 0.7683 | 164 | 2048 | fork pre-identity | 2026-10-17 | ✗ retired |
| 33 | ornith35b (uncensored) | 0.5671 | 164 | 4096 | fork b3-1a33095 | 2026-10-31 | ✓ boot |

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
| 14 | Axion-1.0-35B (IQ3_XXS) | 0.7583 | 120 | 4096 | fork b3-1a33095 | 2026-11-12 | ✓ |
| 15 | gptoss-abliterated | 0.7500 | 120 | 2048 | fork pre-identity | 2026-10-13 | ✓ |
| 16 | Groot-65B-A6B | 0.7500 | 40 | 2048 | bolt b1-a30fb49 | 2026-11-05 | ✗ retired |
| 17 | hy-memory-30b-a3b-q8 | 0.7500 | 120 | 2048 | fork pre-identity | 2026-10-17 | ✗ retired |
| 18 | qwen3next-q4 | 0.7417 | 120 | 2048 | fork b3-1a33095 | 2026-10-31 | ✓ |
| 19 | hy-memory-30b-a3b | 0.7250 | 120 | 2048 | fork pre-identity | 2026-10-17 | ✗ retired |
| 20 | Groot-19B-A3B | 0.7167 | 120 | 4096 | fork b3-1a33095 | 2026-11-11 | ✓ |
| 21 | Laguna-XS-2.1 | 0.7000 (above standard cap) | 40 | 8192 | fork b3-1a33095 | 2026-11-06 | ✓ |
| 22 | mellum | 0.7000 | 120 | 4096 | fork pre-identity | 2026-10-12 | ✗ retired |
| 23 | lfm25-24b-a2b (thinking) | 0.6917 | 120 | 4096 | fork b3-1a33095 | 2026-11-10 | ✓ |
| 24 | lfm25-24b-a2b | 0.6917 | 120 | 4096 | fork pre-identity | 2026-10-17 | ✓ |
| 25 | Lite-Beam-M2.7-229B | 0.6750 | 40 | 4096 | fork b3-1a33095 | 2026-11-08 | ✓ |
| 26 | graft-50b-a3b | 0.6583 | 120 | 2048 | fork pre-identity | 2026-10-19 | ✗ retired |
| 27 | qwen38-35b | 0.6417 | 120 | 4096 | fork b3-1a33095 | 2026-11-01 | ✓ |
| 28 | ornith35b (uncensored) | 0.6333 | 120 | 4096 | fork b3-1a33095 | 2026-10-31 | ✓ boot |
| 29 | Kimi-Linear-48B-A3B-abl | 0.5833 (above standard cap) | 120 | 8192 | fork b3-1a33095 | 2026-11-01 | ✗ retired |
| 30 | kimi | 0.5500 | 120 | 2048 | fork pre-identity | 2026-10-14 | ✗ retired |
| 31 | Ornith-1.5-35B | 0.4417 | 120 | 4096 | fork b3-1a33095 | 2026-11-01 | ✓ |
| 32 | Clover-35B-A3B-Preview | 0.4000 | 120 | 4096 | clover b1-6b9c0cf | 2026-11-03 | ✗ retired |
| 33 | Nemotron-Bolt-74B-A9B | 0.3667 | 120 | 2048 | bolt pre-identity | 2026-10-16 | ✗ retired |

The 26B MoE also leads knowledge. The two 120B-class models recover some ground here and none of it
justifies 60-70 GiB at 23-27 t/s on a box whose best model fits in a sixth of that.

## Reasoning traps — riddles and arithmetic, 14 items

| # | model | riddles | n | cap | build | measured | status |
|---:|---|---:|---:|---:|---|---|---|
| 1 | lfm25-24b-a2b (thinking) | 14/14 | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 2 | gemma4-31b | 14/14 | — | — | fork pre-identity | 2026-10-21 | ✗ retired |
| 3 | gemma4-26b-uncen | 14/14 | — | — | fork b3-1a33095 | 2026-10-28 | ✓ driver |
| 4 | gemma4-26b-a4b | 14/14 | — | — | fork b3-1a33095 | 2026-10-30 | ✗ retired |
| 5 | gemma4-26b-qat-q4 | 14/14 | — | — | fork pre-identity | 2026-10-21 | ✓ |
| 6 | Axion-1.0-35B (IQ3_XXS) | 14/14 | — | — | fork b3-1a33095 | 2026-11-12 | ✓ |
| 7 | qwen3next-q6 | 14/14 | — | — | fork pre-identity | 2026-10-10 | ✓ |
| 8 | qwen3next-q4 | 14/14 | — | — | fork b3-1a33095 | 2026-10-31 | ✓ |
| 9 | gemma-4-12B-QAT | 14/14 | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 10 | qwen38-35b | 14/14 | — | — | fork b3-1a33095 | 2026-11-01 | ✓ |
| 11 | gemma-4-E4B-QAT | 14/14 | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 12 | qwen3-14b | 14/14 | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 13 | qwen3-30b-a3b | 14/14 | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 14 | Clover-35B-A3B-Preview | 14/14 | — | — | clover b1-6b9c0cf | 2026-11-03 | ✗ retired |
| 15 | graft-50b-a3b | 14/14 | — | — | fork pre-identity | 2026-10-19 | ✗ retired |
| 16 | gpt-oss-20b-mxfp4 | 14/14 | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 17 | gemma-4-26B-A4B-QAT + MTP drafter | 14/14 | — | — | fork b3-1a33095 | 2026-11-09 | ✓ |
| 18 | Nemotron-Bolt-74B-A9B | 13/14 | — | — | bolt pre-identity | 2026-10-16 | ✗ retired |
| 19 | Groot-19B-A3B | 13/14 | — | — | fork b3-1a33095 | 2026-11-11 | ✓ |
| 20 | Kimi-Linear-48B-A3B-abl | 13/14 | — | — | fork b3-1a33095 | 2026-11-01 | ✗ retired |
| 21 | Ornith-1.5-35B | 13/14 | — | — | fork b3-1a33095 | 2026-11-01 | ✓ |
| 22 | qwen3-8b | 13/14 | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 23 | kimi | 13/14 | — | — | fork pre-identity | 2026-10-14 | ✗ retired |
| 24 | ornith-122b | 12/14 | — | — | fork pre-identity | 2026-10-20 | ✓ |
| 25 | gptoss | 12/14 | — | — | fork pre-identity | 2026-10-12 | ✓ |
| 26 | qwen35 | 12/14 | — | — | fork pre-identity | 2026-10-11 | ✗ retired |
| 27 | qwen36-35b | 12/14 | — | — | fork pre-identity | 2026-10-12 | ✗ retired |
| 28 | mistral-small-3.1-24b | 12/14 | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 29 | hy-memory-30b-a3b | 12/14 | — | — | fork pre-identity | 2026-10-17 | ✗ retired |
| 30 | ornith35b (uncensored) | 12/14 | — | — | fork b3-1a33095 | 2026-10-31 | ✓ boot |
| 31 | nemotron-super-120b | 11/14 | — | — | bolt pre-identity | 2026-10-18 | ✗ retired |
| 32 | ornith-mtp-21g | 11/14 | — | — | fork pre-identity | 2026-10-17 | ✓ |
| 33 | Swift-1.5-FN-Heretic | 11/14 | — | — | fork b3-1a33095 | 2026-11-05 | ✓ |
| 34 | mellum | 11/14 | — | — | fork pre-identity | 2026-10-12 | ✗ retired |
| 35 | qwen38fn-abl | 11/14 | — | — | fork pre-identity | 2026-10-13 | ✓ |
| 36 | hy-memory-30b-a3b-q8 | 11/14 | — | — | fork pre-identity | 2026-10-17 | ✗ retired |
| 37 | Ling-3.0-flash | 11/14 | — | — | fork pre-identity | 2026-10-22 | ✗ retired |
| 38 | minicpm-v47-35b | 10/14 | — | — | bolt pre-identity | 2026-10-18 | ✓ |
| 39 | gptoss-abliterated | 10/14 | — | — | fork pre-identity | 2026-10-13 | ✓ |
| 40 | flint (i1-Q4_K_M) | 10/14 | — | — | flint pre-identity | 2026-10-25 | ✗ retired |
| 41 | mellum21-fork | 10/14 | — | — | fork pre-identity | 2026-10-18 | ✗ retired |
| 42 | Laguna-XS-2.1 | 10/14 | — | — | fork b3-1a33095 | 2026-11-06 | ✓ |
| 43 | lfm25-24b-a2b | 10/14 | — | — | fork pre-identity | 2026-10-17 | ✓ |
| 44 | Axion-1.0-35B | 10/14 | — | — | fork b3-1a33095 | 2026-11-05 | ✓ |
| 45 | Lite-Beam-M2.7-229B | 10/14 | — | — | fork b3-1a33095 | 2026-11-08 | ✓ |
| 46 | Groot-65B-A6B | 9/14 | — | — | bolt b1-a30fb49 | 2026-11-05 | ✗ retired |
| 47 | nemotron-bolt (broken load) | 8/14 | — | — | fork pre-identity | 2026-10-21 | ✗ retired |

Fourteen hand-written riddles and three arithmetic traps. Not a benchmark in the psychometric sense: it
catches a model that pattern-matches an answer without following the question, which is exactly the
failure the code and knowledge axes do not show. `14/14` is the ceiling; several strong coders score
10-11 because they answer confidently and wrongly.

## Speed — decode tokens/second

| # | model | decode | n | cap | build | measured | status |
|---:|---|---:|---:|---:|---|---|---|
| 1 | mellum21-fork | 111.9 t/s | — | — | fork pre-identity | 2026-10-18 | ✗ retired |
| 2 | lfm25-24b-a2b (thinking) | 111.2 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 3 | lfm25-24b-a2b | 106.6 t/s | — | — | fork pre-identity | 2026-10-17 | ✓ |
| 4 | Axion-1.0-35B (IQ3_XXS) | 93.8 t/s | — | — | fork b3-1a33095 | 2026-11-12 | ✓ |
| 5 | mellum | 91.8 t/s | — | — | fork pre-identity | 2026-10-12 | ✗ retired |
| 6 | Laguna-XS-2.1 | 87.7 t/s | — | — | fork b3-1a33095 | 2026-11-06 | ✓ |
| 7 | qwen3-30b-a3b | 79.7 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 8 | Axion-1.0-35B | 76.2 t/s | — | — | fork b3-1a33095 | 2026-11-05 | ✓ |
| 9 | qwen38-35b | 74.8 t/s | — | — | fork b3-1a33095 | 2026-11-01 | ✓ |
| 10 | Kimi-Linear-48B-A3B-abl | 74.8 t/s | — | — | fork b3-1a33095 | 2026-11-01 | ✗ retired |
| 11 | hy-memory-30b-a3b | 74.7 t/s | — | — | fork pre-identity | 2026-10-17 | ✗ retired |
| 12 | gpt-oss-20b-mxfp4 | 74.4 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 13 | Ornith-1.5-35B | 74.1 t/s | — | — | fork b3-1a33095 | 2026-11-01 | ✓ |
| 14 | Nemotron-Bolt-74B-A9B | 72.8 t/s | — | — | bolt pre-identity | 2026-10-16 | ✗ retired |
| 15 | flint (i1-Q4_K_M) | 71.1 t/s | — | — | flint pre-identity | 2026-10-25 | ✗ retired |
| 16 | ornith35b (uncensored) | 69.9 t/s | — | — | fork b3-1a33095 | 2026-10-31 | ✓ boot |
| 17 | kimi | 67.4 t/s | — | — | fork pre-identity | 2026-10-14 | ✗ retired |
| 18 | ornith-mtp-21g | 65.2 t/s | — | — | fork pre-identity | 2026-10-17 | ✓ |
| 19 | Groot-19B-A3B | 64.8 t/s | — | — | fork b3-1a33095 | 2026-11-11 | ✓ |
| 20 | minicpm-v47-35b | 64.6 t/s | — | — | bolt pre-identity | 2026-10-18 | ✓ |
| 21 | gemma4-26b-qat-q4 | 59.5 t/s | — | — | fork pre-identity | 2026-10-21 | ✓ |
| 22 | qwen3next-q4 | 58.1 t/s | — | — | fork b3-1a33095 | 2026-10-31 | ✓ |
| 23 | gemma-4-E4B-QAT | 57.8 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 24 | qwen36-35b | 57.1 t/s | — | — | fork pre-identity | 2026-10-12 | ✗ retired |
| 25 | gemma4-26b-uncen | 56.9 t/s | — | — | fork b3-1a33095 | 2026-10-28 | ✓ driver |
| 26 | gemma-4-26B-A4B-QAT + MTP drafter | 54.9 t/s | — | — | fork b3-1a33095 | 2026-11-09 | ✓ |
| 27 | graft-50b-a3b | 54.3 t/s | — | — | fork pre-identity | 2026-10-19 | ✗ retired |
| 28 | Clover-35B-A3B-Preview | 53.7 t/s | — | — | clover b1-6b9c0cf | 2026-11-03 | ✗ retired |
| 29 | qwen38fn-abl | 52.9 t/s | — | — | fork pre-identity | 2026-10-13 | ✓ |
| 30 | hy-memory-30b-a3b-q8 | 52.3 t/s | — | — | fork pre-identity | 2026-10-17 | ✗ retired |
| 31 | gptoss-abliterated | 50.5 t/s | — | — | fork pre-identity | 2026-10-13 | ✓ |
| 32 | gptoss | 50.1 t/s | — | — | fork pre-identity | 2026-10-12 | ✓ |
| 33 | gemma4-26b-a4b | 49.4 t/s | — | — | fork b3-1a33095 | 2026-10-30 | ✗ retired |
| 34 | qwen3next-q6 | 45.8 t/s | — | — | fork pre-identity | 2026-10-10 | ✓ |
| 35 | Ling-3.0-flash | 43.5 t/s | — | — | fork pre-identity | 2026-10-22 | ✗ retired |
| 36 | qwen3-8b | 39.0 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 37 | Lite-Beam-M2.7-229B | 34.1 t/s | — | — | fork b3-1a33095 | 2026-11-08 | ✓ |
| 38 | gemma-4-12B-QAT | 27.8 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 39 | Groot-65B-A6B | 27.6 t/s | — | — | bolt b1-a30fb49 | 2026-11-05 | ✗ retired |
| 40 | nemotron-super-120b | 27.1 t/s | — | — | bolt pre-identity | 2026-10-18 | ✗ retired |
| 41 | Swift-1.5-FN-Heretic | 25.6 t/s | — | — | fork b3-1a33095 | 2026-11-05 | ✓ |
| 42 | qwen3-14b | 23.5 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 43 | ornith-122b | 23.3 t/s | — | — | fork pre-identity | 2026-10-20 | ✓ |
| 44 | qwen35 | 22.9 t/s | — | — | fork pre-identity | 2026-10-11 | ✗ retired |
| 45 | nemotron-bolt (broken load) | 22.7 t/s | — | — | fork pre-identity | 2026-10-21 | ✗ retired |
| 46 | qwen38fn32-prune2 | 20.0 t/s | — | — | qwen4exp-var b1-1844325 | 2026-11-03 | ✗ retired |
| 47 | gemma4-31b | 17.0 t/s | — | — | fork pre-identity | 2026-10-21 | ✗ retired |
| 48 | mistral-small-3.1-24b | 14.9 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |

Decode is bandwidth-bound on this platform (~256 GB/s shared with the CPU), so it tracks active
parameters, not total parameters. The top of this table is two ~12-24B MoEs; the bottom is a 120B.

## Prefill — prompt tokens/second

| # | model | prefill | n | cap | build | measured | status |
|---:|---|---:|---:|---:|---|---|---|
| 1 | lfm25-24b-a2b (thinking) | 3360 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 2 | lfm25-24b-a2b | 2930 t/s | — | — | fork pre-identity | 2026-10-17 | ✓ |
| 3 | mellum21-fork | 2723 t/s | — | — | fork pre-identity | 2026-10-18 | ✗ retired |
| 4 | mellum | 2442 t/s | — | — | fork pre-identity | 2026-10-12 | ✗ retired |
| 5 | gemma-4-E4B-QAT | 2243 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 6 | Groot-19B-A3B | 2176 t/s | — | — | fork b3-1a33095 | 2026-11-11 | ✓ |
| 7 | gpt-oss-20b-mxfp4 | 2169 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 8 | qwen3-30b-a3b | 1910 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 9 | gemma4-26b-qat-q4 | 1900 t/s | — | — | fork pre-identity | 2026-10-21 | ✓ |
| 10 | gemma-4-26B-A4B-QAT + MTP drafter | 1886 t/s | — | — | fork b3-1a33095 | 2026-11-09 | ✓ |
| 11 | Kimi-Linear-48B-A3B-abl | 1774 t/s | — | — | fork b3-1a33095 | 2026-11-01 | ✗ retired |
| 12 | ornith35b (uncensored) | 1762 t/s | — | — | fork b3-1a33095 | 2026-10-31 | ✓ boot |
| 13 | gemma4-26b-uncen | 1759 t/s | — | — | fork b3-1a33095 | 2026-10-28 | ✓ driver |
| 14 | Ornith-1.5-35B | 1633 t/s | — | — | fork b3-1a33095 | 2026-11-01 | ✓ |
| 15 | ornith-mtp-21g | 1610 t/s | — | — | fork pre-identity | 2026-10-17 | ✓ |
| 16 | minicpm-v47-35b | 1600 t/s | — | — | bolt pre-identity | 2026-10-18 | ✓ |
| 17 | kimi | 1597 t/s | — | — | fork pre-identity | 2026-10-14 | ✗ retired |
| 18 | qwen38-35b | 1550 t/s | — | — | fork b3-1a33095 | 2026-11-01 | ✓ |
| 19 | qwen36-35b | 1548 t/s | — | — | fork pre-identity | 2026-10-12 | ✗ retired |
| 20 | Axion-1.0-35B (IQ3_XXS) | 1543 t/s | — | — | fork b3-1a33095 | 2026-11-12 | ✓ |
| 21 | hy-memory-30b-a3b | 1515 t/s | — | — | fork pre-identity | 2026-10-17 | ✗ retired |
| 22 | Clover-35B-A3B-Preview | 1461 t/s | — | — | clover b1-6b9c0cf | 2026-11-03 | ✗ retired |
| 23 | hy-memory-30b-a3b-q8 | 1459 t/s | — | — | fork pre-identity | 2026-10-17 | ✗ retired |
| 24 | Axion-1.0-35B | 1422 t/s | — | — | fork b3-1a33095 | 2026-11-05 | ✓ |
| 25 | graft-50b-a3b | 1368 t/s | — | — | fork pre-identity | 2026-10-19 | ✗ retired |
| 26 | Laguna-XS-2.1 | 1321 t/s | — | — | fork b3-1a33095 | 2026-11-06 | ✓ |
| 27 | qwen3-8b | 1300 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 28 | qwen3next-q4 | 1219 t/s | — | — | fork b3-1a33095 | 2026-10-31 | ✓ |
| 29 | qwen3next-q6 | 1189 t/s | — | — | fork pre-identity | 2026-10-10 | ✓ |
| 30 | gptoss-abliterated | 1052 t/s | — | — | fork pre-identity | 2026-10-13 | ✓ |
| 31 | gptoss | 1045 t/s | — | — | fork pre-identity | 2026-10-12 | ✓ |
| 32 | gemma-4-12B-QAT | 911 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 33 | qwen3-14b | 743 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 34 | qwen35 | 622 t/s | — | — | fork pre-identity | 2026-10-11 | ✗ retired |
| 35 | ornith-122b | 605 t/s | — | — | fork pre-identity | 2026-10-20 | ✓ |
| 36 | Groot-65B-A6B | 597 t/s | — | — | bolt b1-a30fb49 | 2026-11-05 | ✗ retired |
| 37 | nemotron-bolt (broken load) | 586 t/s | — | — | fork pre-identity | 2026-10-21 | ✗ retired |
| 38 | Nemotron-Bolt-74B-A9B | 577 t/s | — | — | bolt pre-identity | 2026-10-16 | ✗ retired |
| 39 | Swift-1.5-FN-Heretic | 512 t/s | — | — | fork b3-1a33095 | 2026-11-05 | ✓ |
| 40 | mistral-small-3.1-24b | 460 t/s | — | — | fork b3-1a33095 | 2026-11-10 | ✓ |
| 41 | qwen38fn-abl | 448 t/s | — | — | fork pre-identity | 2026-10-13 | ✓ |
| 42 | nemotron-super-120b | 411 t/s | — | — | bolt pre-identity | 2026-10-18 | ✗ retired |
| 43 | qwen38fn32-prune2 | 397 t/s | — | — | qwen4exp-var b1-1844325 | 2026-11-03 | ✗ retired |
| 44 | gemma4-31b | 350 t/s | — | — | fork pre-identity | 2026-10-21 | ✗ retired |
| 45 | Lite-Beam-M2.7-229B | 261 t/s | — | — | fork b3-1a33095 | 2026-11-08 | ✓ |

Prefill is shader-bound and moves far more between builds than decode does. Use it to size long-prompt
work, not to rank models generally.

---

## Floors — HumanEval measured below the 2048-token standard

| # | model | HumanEval | n | cap | build | measured | status |
|---:|---|---:|---:|---:|---|---|---|
| 1 | gemma-4-12B-QAT | 0.8963 **floor** | 164 | 512 | fork b3-1a33095 | 2026-11-10 | ✓ |
| 2 | gemma-4-E4B-QAT | 0.8659 **floor** | 164 | 512 | fork b3-1a33095 | 2026-11-10 | ✓ |
| 3 | qwen3-14b | 0.8537 **floor** | 164 | 512 | fork b3-1a33095 | 2026-11-10 | ✓ |
| 4 | qwen3-30b-a3b | 0.8537 **floor** | 164 | 512 | fork b3-1a33095 | 2026-11-10 | ✓ |
| 5 | mistral-small-3.1-24b | 0.8232 **floor** | 164 | 512 | fork b3-1a33095 | 2026-11-10 | ✓ |
| 6 | qwen3-8b | 0.7866 **floor** | 164 | 512 | fork b3-1a33095 | 2026-11-10 | ✓ |
| 7 | gpt-oss-20b-mxfp4 | 0.5854 **floor** | 164 | 512 | fork b3-1a33095 | 2026-11-10 | ✓ |
| 8 | nemotron-bolt (broken load) | 0.1786 **floor** | 56 | 512 | fork pre-identity | 2026-10-21 | ✗ retired |

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
