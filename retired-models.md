# Retired local models — restore recipes
> Part of [Local LLM benchmarks on AMD Strix Halo](index.html). Every deletion here is reversible: each entry carries file sizes, sha256s, the upstream repo and the flags that worked.


Kept so a deletion is reversible without re-researching URLs, hashes and flags.

## Instella-MoE-16B-A3B-Think (retired 2026-10-12)

Removed at the user's request: the weights, its unit, run script, switch entry, log files, and
the bespoke `instella-moe` llama.cpp fork tree it needed.

What was removed:

    ~/llama-local/models/Instella-MoE-16B-A3B-Think-Q4_K_M.gguf   10,470,249,600 B (9.75 GiB)
    ~/llama-local/llama-instella-test/                            644 MB (fork build tree)
    ~/llama-local/run-instella.sh                                 the unit's ExecStart
    ~/llama-local/instella-download.log, instella.log, instella-server.log
    ~/.config/systemd/user/llama-instella.service                 (was disabled, never the boot unit)
    llama-switch entry `instella` (:8087) + its usage string
    llama-instella.service from every other unit's Conflicts= line

Reason to distrust that copy anyway: the local file was **10,470,249,600 B** while the current
HF artifact is **10,470,249,472 B** — 128 bytes larger, so the on-disk file did not match the
published artifact. Not a byte-for-byte clean download.

Restore (weights are public; the arch is NOT in upstream llama.cpp or the halo-box fork, so the
bespoke fork is required — see the skill's `references/instella-moe.md` for the build):

    cd ~/llama-local/models && wget -c \
      https://huggingface.co/NANI-Nithin/Instella-MoE-16B-A3B-Think-GGUF/resolve/main/Instella-MoE-16B-A3B-Think-Q4_K_M.gguf
    # expected: 10,470,249,472 B, sha256 8b1f2759d3415850ffc3b87edf2c339936718805651f09945016e8676a135f81
    # (verify with sha256sum against that LFS oid before serving)

Then re-create the unit on :8087 (free again now) with the usual template, re-add
`llama-instella.service` to every peer unit's Conflicts= line, rebuild the fork, and add the
`instella` case back to llama-switch.

## Hermes-3-Llama-3.1-70B-Uncensored — retired 2026-10-13, never served

    ~/llama-local/models/Hermes-3-Llama-3.1-70B-Uncensored.i1-Q4_K_M.gguf   42,520,399,008 B (39.6 GiB)
    ~/llama-local/models/Hermes-3-70B-uncensored/                            partial fp16 tree (1.8 GB)
    ~/llama-local/fetch-hermes3-gguf.sh, fetch-hermes3-70b.sh, run-hermes3-70b.sh
    ~/llama-local/hermes3-70b-download.log, hermes3-70b-gguf-download.log
    ~/.config/systemd/user/llama-hermes3-70b.service          (:8087; wired, never started)
    llama-switch entry `hermes3-70b` + its usage string
    llama-hermes3-70b.service from every other unit's Conflicts= line

Deleted on request while the download was at ~90%: the unit was built and never started, so no
run data, no benchmark, and no log worth keeping. Port :8087 returned to the free pool.

Restore (weights are public; the arch is plain `llama`, so the halo-box fork serves it — no bespoke
build. This is a 70B DENSE model: 80 layers, 64 heads / 8 KV heads, so KV is 160 KiB/token at q8_0
and it wants the 100 GiB GTT pool to itself: 39.6 GiB weights + 20 GiB KV at 131072 ctx):

    ~/llama-local/hf-fetch.sh mradermacher/Hermes-3-Llama-3.1-70B-Uncensored-i1-GGUF Hermes-3-Llama-3.1-70B-Uncensored.i1-Q4_K_M.gguf
    # expected 42520399008 B, sha256 ca2e201e8a780b9e40d3b59c95756f8a5364443f783d802696fb828d40e82747
    #   (hf-fetch.sh verifies size + sha256 against the API's LFS metadata)
    # run script: llama-server -m <file> --host 127.0.0.1 --port 8087 --alias hermes3-70b \
    #   -ngl 99 -c 131072 --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0 \
    #   --spec-type none --reasoning off -np 1 --metrics

The upstream repo the model was requested from (Guilherme34/Hermes-3-Llama-3.1-70B-Uncensored) is
**fp16 safetensors only** — 131.43 GiB across 30 shards, no GGUF — so serving it from source needs
convert_hf_to_gguf.py (torch + transformers, neither installed) plus llama-quantize. The quant used
above is mradermacher's imatrix build of that exact fine-tune (base_model declared on its card).
Its model card also says the "uncensored" behaviour only appears with a specific system prompt; that
prompt was never set on any channel here.

## Meta Muse Glimmer-30B — retired 2026-10-13

Dense 30B causal LM + perception encoder, Apache-2.0, Meta Superintelligence Lab, Aug 2026 (distilled
from "Muse Spark", agentic framing). Retired after a full evening's evaluation.

**Restore recipe** — repo `meta-models/Muse-Glimmer-30B-GGUF`, all four files, and sha256-check each
after fetching (these hashes were computed from the verified local copies; the HF `lfs.oid` is the same
value by definition, and each prefix matched what the fetch logged at download time):

- `Muse-Glimmer-30B-KQuant-Dynamic-Q4_K_XL.gguf`
  - 19,653,960,832 bytes, sha256 `ac7023d6a4c704eb9af54ab53e476a66b7f5b6c0ef2fc4a8dde5253c291a6c38`
  - https://huggingface.co/meta-models/Muse-Glimmer-30B-GGUF/resolve/main/Muse-Glimmer-30B-KQuant-Dynamic-Q4_K_XL.gguf
  - 18.30 GiB, the default quant; the one every measurement below used
- `Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf`
  - 16,756,683,904 bytes, sha256 `4cc57c0f51040a226e5a72cc47b7613f7772950e460a665f7083de89f183f60e`
  - https://huggingface.co/meta-models/Muse-Glimmer-30B-GGUF/resolve/main/Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf
  - 15.61 GiB, the smaller/faster-quality-trade variant; never benchmarked
- `dflash-Muse-Glimmer-30B-Q4_K_M.gguf`
  - 1,631,208,128 bytes, sha256 `b2e808bf656086fe86bd0d0bd990f01d33e377537a07c02d45371517c8b264ef`
  - https://huggingface.co/meta-models/Muse-Glimmer-30B-GGUF/resolve/main/dflash-Muse-Glimmer-30B-Q4_K_M.gguf
  - 1.52 GiB DFlash drafter; architecture `dflash`, 58 tensors, 5 layers
- `mmproj-Muse-Glimmer-30B-Q4_K_M.gguf`
  - 1,400,328,928 bytes, sha256 `f48b452316f9b213758e8659444029b961a24a07f99a1abb2a9f88b06f7c00c6`
  - https://huggingface.co/meta-models/Muse-Glimmer-30B-GGUF/resolve/main/mmproj-Muse-Glimmer-30B-Q4_K_M.gguf
  - 1.30 GiB vision projector; verified 3/3 on the shape probe

- unit `llama-muse-glimmer.service`, port **:8098**, alias `muse-glimmer`, script `run-muse-glimmer.sh`
- flags: `-m <KQuant> --mmproj <mmproj> -ngl 99 -c 131072 --flash-attn on --cache-type-k/v q8_0
  --reasoning auto -np 1 --metrics`; the script carries a `VISION` (default on) and a `DFLASH=0|1` switch
- arch `muse_glimmer` works on the halo-box fork (`src/models/muse-glimmer.cpp`) and mtmd has a
  `muse_glimmer` clip graph; served weights were 18.3 GiB with only ~14.7 GiB of GTT in use

**Why retired — measured, not assumed:**

| axis | result |
|---|---|
| speed, 3x512 greedy probe (median) | **10.77 t/s** — perf axis 10.9, pp 374, ttft 4.93 s |
| DFlash (`--spec-type draft-dflash`) | **0 draft tokens** — `spec_decode_num_draft_tokens_total 0` after a 256-token generation; tg identical to 0.00%. Invocation verified correct via `bash -x`, sidecar verified real. The card's 1.5x-3.1x is untestable here |
| riddles (core, default cap) | 8/14, weakest in the fleet; `-rea off` did not change it |
| long-form answers | "count to 40 in words" returns EMPTY `content` after burning 256 tokens on a prompt echo — with and without `-rea off` |
| needles | PASS / PASS |

- `-rea off` A/B (server-side `--reasoning off`, same weights): riddles **8/14, identical**, perf pp 366.8 /
  tg 10.9, and the long-form prompt still returns EMPTY content. So the weak core score is the model as
  served, NOT a reasoning-budget artifact — my interim hypothesis was wrong and this is the check that
  refuted it. (`--no-reasoning-preserve` remains untested; `-rea off` is the flag that made no difference.)

Reason it went: **no niche.** Dense 30B at Q4 on a bandwidth-bound box is inherently ~11 t/s here, its
one distinctive feature produced nothing, and big + uncensored + vision + MTP is already covered by the
Flash-Next GSQ-RCO abliterated (:8097) at roughly 3-5x the throughput and less GTT.

## 2026-10-17 batch — six superseded models (disk-audit queue, `~/llama-local/DELETE-QUEUE.md`)

Retired on the user's explicit instruction after the four eligibility rules were applied: not a former
daily driver (>12 h), not favoured, no kept model depends on the files, results recorded first.
Every local artifact was hashed before deletion and **11 of the 12 matched the repo's published LFS oid
exactly** — the one exception is the Fable weights, whose source repo was never recorded (noted below).

Units, run scripts, llama-switch cases and the Hermes aliases pointing at them were removed in the same
change (registry 19 → 13 units, `Conflicts=` regenerated and verified 13 × 12, no mismatches).

### Qwen3.8-27B TurboFCFusion-735-882-Here-Uncen-NEO-CODER-MAX-MTP ("Fable") — retired 2026-10-17
Files (size, sha256):
    ~/llama-local/models/Qwen3.8-27B-TurboFCFusion-735-882-Here-Uncen-NEO-CODER-MAX-MTP-Q4_K_M.gguf
      18,498,573,856 B  (18.50 GB)  sha256 bc7a6cf2bcc78d1190aaf04d1ab1c5cb845b6ff23aa0e7d24fe0d2ea6d3a7c7c
    ~/llama-local/models/mmproj-F16.gguf
      927,606,976 B  (0.93 GB)  sha256 82e620db8cb83267e9775e5aad3e8d8aa5af7ace825e94c52d3d730eb35af88a

Measured: pp 367, tg 12.0 t/s, ttft 5.0 s, riddles 11/14 — **UNRANKED: never completed an axis**

Source / restore: **source repo NOT recorded at fetch time.** The only TurboFCFusion GGUF repo the Hub now shows is
`bbkdevops/Qwen3.8-27B-TurboFCFusion-CyberSec`, and it publishes **IQ4_NL (17.75 GB)**, not this Q4_K_M.
Restoring this exact file requires finding it by basename; the IQ4_NL is the closest available substitute.

Evidence on file: 2026-10-12 suite + 2 run artifacts in ~/runs
Also removed: unit `llama-qwen38-27b-fable.service` (: 8095), its run script, its llama-switch case, its log,
and any Hermes alias pointing at :8095.

### Qwen3.6-35B-A3B UD-Q4_K_XL — retired 2026-10-17
Files (size, sha256):
    ~/llama-local/models/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf
      22,360,456,160 B  (22.36 GB)  sha256 707a55a8a4397ecde44de0c499d3e68c1ad1d240d1da65826b4949d1043f4450

Measured: HE 0.8354 (cap 1024), MMLU-Pro 0.4500 (512), IFEval 0.867, riddles 12/14, pp 1548, tg 57.1

Source / restore: `https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF/resolve/main/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf`

Evidence on file: row in the 2026-10-12 eight-model suite; 4 run files in ~/runs
Also removed: unit `llama-qwen36-35b.service` (: 8092), its run script, its llama-switch case, its log,
and any Hermes alias pointing at :8092.

### Qwen3.8-27B Q6_K_L (Hermes alias `qwen38`) — retired 2026-10-17
Files (size, sha256):
    ~/llama-local/models/Qwen3.8-27B-Q6_K_L.gguf
      24,958,908,128 B  (24.96 GB)  sha256 e8750bb81ba49f90eb68df99776b250dbc14666043098952de6422cbecd77a21

Measured: **never scored on HumanEval or MMLU**; riddles-only data from 2026-09-03/09-11 passes; ~9 t/s

Source / restore: `https://huggingface.co/bartowski/Qwen3.8-27B-GGUF/resolve/main/Qwen3.8-27B-Q6_K_L.gguf`

Evidence on file: 7 run files in ~/runs (riddle/depth passes only)
Also removed: unit `llama-qwen38.service` (: 8088), its run script, its llama-switch case, its log,
and any Hermes alias pointing at :8088.

### Kolibri-1 78B-A3.46B Q5_K_M — retired 2026-10-17
Files (size, sha256):
    ~/llama-local/models/Q5_K_M/Kolibri-1-Q5_K_M-00001-of-00002.gguf
      44,739,588,864 B  (44.74 GB)  sha256 857961501f9fc8847f37535c8cdfe0cd4c3ab064bb4cadbd4896c3d3824712f9
    ~/llama-local/models/Q5_K_M/Kolibri-1-Q5_K_M-00002-of-00002.gguf
      10,849,180,800 B  (10.85 GB)  sha256 929c6b679d7739e7617089a346d499c8b28f8699f7247432d0f5ebdf4f9252a2

Measured: HE 0.8293 (512, 0 rows at cap), MMLU-Pro 0.4000 (512, think-off arm), riddles 11/14 real, pp 1275-1295, tg 60.5
**Only German-capable (En/De) model on this box** — if German is ever needed, this is what to restore first.

Source / restore: `https://huggingface.co/Hob-forge/Kolibri-1-GGUF/resolve/main/Q5_K_M/<shard>` (2 shards, same dir)

Evidence on file: `references/2026-10-14-kolibri-kimi-round.md` + 6 run files
Also removed: unit `llama-kolibri.service` (: 8098), its run script, its llama-switch case, its log,
and any Hermes alias pointing at :8098.

### Qwen3.5-122B-A10B UD-Q4_K_XL — retired 2026-10-17
Files (size, sha256):
    ~/llama-local/models/Qwen3.5-122B-A10B-UD-Q4_K_XL-00001-of-00003.gguf
      10,943,552 B  (0.01 GB)  sha256 467c9bd92ea518539cf75bf5a5fbfbd35e9a0b40d766ccaa67bf120e12041df3
    ~/llama-local/models/Qwen3.5-122B-A10B-UD-Q4_K_XL-00002-of-00003.gguf
      49,640,779,424 B  (49.64 GB)  sha256 ecdbd42d43b0df9fa0ef9a584e09e95a43966ef03a122aba0b87a99d44d9ad98
    ~/llama-local/models/Qwen3.5-122B-A10B-UD-Q4_K_XL-00003-of-00003.gguf
      27,378,273,056 B  (27.38 GB)  sha256 13300e0f059e6fa21aa0fabde2a554f9deea366c0e54f268045769b214b28c97

Measured: HE 0.9242 (n=66), MMLU-Pro 0.5417 (512), **IFEval 0.917 — best of any local model measured here**, riddles 12/14,
pp 622, tg 22.9 (≈3 min to first token at 4k prompt: the reason it lost its slot)

Source / restore: `https://huggingface.co/unsloth/Qwen3.5-122B-A10B-GGUF/resolve/main/UD-Q4_K_XL/<shard>` (3 shards)

Evidence on file: row in the 2026-10-12 suite; 5 run files
Also removed: unit `llama-qwen35moe.service` (: 8084), its run script, its llama-switch case, its log,
and any Hermes alias pointing at :8084.

### Qwen3.8-Flash-Next UD-Q2_K_XL — retired 2026-10-17
Files (size, sha256):
    ~/llama-local/models/Qwen3.8-Flash-Next-UD-Q2_K_XL-00001-of-00003.gguf
      10,946,624 B  (0.01 GB)  sha256 a4f3b21e77353999829f2f767e9ac21ce9c71d29a74f2cc9eda48c9bf23c8b86
    ~/llama-local/models/Qwen3.8-Flash-Next-UD-Q2_K_XL-00002-of-00003.gguf
      49,979,779,296 B  (49.98 GB)  sha256 2e3bf1ee7d2a04e261e9f342a2d968f696cce5941d082b0e434deb9b1edc12c6
    ~/llama-local/models/Qwen3.8-Flash-Next-UD-Q2_K_XL-00003-of-00003.gguf
      28,878,402,944 B  (28.88 GB)  sha256 ec8c106759fdf4f463039c34c0707718d7d8908d53d892bd4f002e71620803f9

Measured: **never scored on HumanEval or MMLU on the current suite**; riddles 5/5 on the 2026-09-11 pass; ~30 t/s;
79 GB spent on a 2-bit quant. The measured Flash-Next numbers on this box belong to its **protected
abliterated sibling (":8097", `IQ3_S/`), which is kept** — that is where to look for real scores.

Source / restore: `https://huggingface.co/unsloth/Qwen3.8-Flash-Next-GGUF/resolve/main/UD-Q2_K_XL/<shard>` (3 shards)

Evidence on file: `references/qwen38flashnext-20260911.md` + 8 run files
Also removed: unit `llama-qwen38fn.service` (: 8089), its run script, its llama-switch case, its log,
and any Hermes alias pointing at :8089.

Batch total: 278233439680.00 GB of weights (plus 9.67 GB of junk
removed in the same pass). Disk after: see `df -h /home`; the btrfs snapshot holds roughly 30 GB back
until it rotates.

Restore procedure (generic): re-download to the exact path above, `sha256sum` it against the recorded
hash, then re-create the unit from the standard template, re-add it to every peer's `Conflicts=` line,
add the `llama-switch` case, and — if a Hermes alias was removed — re-add `providers.<name>` plus
`model_aliases.<name>` and restart the gateway.

## flint (RecursiveSI/flint) — retired 2026-10-24, measured, not dominated

**Why retired:** it is a *good* model that is still strictly dominated by the daily driver.
HumanEval 0.9167 (55/60) at cap 4096 vs gemma4-26b QAT 0.9390 and Ornith-122B 0.9512; riddles
10/14 vs 14/14 for gemma/Ornith/Kimi; decode 60.4 t/s vs 67 (gemma QAT) and 70 (Ornith 35B).
Its only distinguishing axis, 262k native context, is covered by Kimi-Linear (1M, faster, 14/14).

**Measured before deletion (t20, same harness, cap 4096):**
- perf: pp 1433 t/s (1914 on the second run), tg 60.4 t/s, ttft 1248 ms @1789-token prompt
- preflight 3/3, needle 2k PASS, needle 8k PASS, riddles 10/14 (4 misses = EMPTY content, cap-limited)
- humaneval pass@1 = 0.9167 (55/60), wall 1061 s
- raw: `~/runs/20261025-063840-flint-q4-official.jsonl`, `~/runs/20261025-070907-flint-q4-he60.jsonl`,
  logs `~/llama-local/t20-flint-q4-official.log`, `~/llama-local/t20-flint-he60.log`

**Restore recipe**
- weights: `flint-preview-UD-Q4_K_XL.gguf`, 25,054,688,704 B, sha256
  `63c2ecc461ca545134b670c660e76fa20f47240f8d39b6510bfd21c4dd6e072f`
  = `unsloth/flint-GGUF` → `flint-UD-Q4_K_XL.gguf` (repo LFS oid 63c2ecc461ca). Note the local
  filename says "preview" but the sha IS the official UD-Q4_K_XL; do not re-fetch a "release".
  Other levels in that repo: IQ1_M 10.57, IQ2_XXS 11.04, Q2_K_XL 12.63, IQ3_XXS 13.54,
  Q3_K_XL 17.22, Q5_K_XL 27.86, Q6_K_XL 33.83, Q8_0 39.40, BF16 74.12 GiB.
- unit `llama-flint-preview.service`, port **8183** (now free), alias `flint`, script `run-flint.sh`:
  `-ngl 99 -c 131072 --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0 --jinja -np 1 -b 4096 -ub 2048`
- arch `flint` (49 blocks, 2 dense + 47 MoE, 256 experts / 6 used / 2 shared, hidden 2048,
  ctx_train 262144, sliding window 513 on 35 layers, 32 q / 4 kv heads).
- **bespoke build required:** arch `flint` is NOT in the halo-box fork. Built tree was
  `flint-pr-llama.cpp` (PR #30928, commit 1b44e30); it was deleted with this retirement because
  the only other script pointing at it (`run-mammoth.sh`) had no weights left either (also removed).
  Rebuild: clone llama.cpp, apply/merge PR #30928, Vulkan configure (see the fork's configure line),
  targets `llama-server`.
- Also removed with it: `run-mammoth.sh` (orphan — `models/mammoth-1.*` were already gone).

## sage-a1.5 and groot-19b-a3b — retired 2026-10-25 (measured, neither was placed)
Both fetched, wired (units 25/26, ports 8183/8189) and fully measured the same day, then retired:
neither takes the daily-driver slot, and only sage had a defensible niche (fast vision + 262k ctx).
User decision: delete both.

### Measured before deletion (all on the halo-box fork, ctx 131072, q8_0 KV, Q4_K_M)
- **Sage-A1.5, thinking OFF** (`--chat-template-kwargs '{"enable_thinking":false}'`): pp 1690 / tg 74.6 /
  ttft 1064 ms @1799 tok; preflight 3/3; needle 2k PASS, 8k PASS; **riddles 14/14**;
  **HumanEval 0.8659 (142/164)** in 270 s (1.6 s/item); **MMLU-Pro 0.6250 (75/120)** in 992 s.
  A `--limit 60` subset read 0.9167 (55/60) — ~5pp optimistic, do not compare to 164-item cells.
- **Sage-A1.5, thinking ON (template default, UNUSABLE):** 20/20 HumanEval FAILs at ~53 s/item, every
  item burning the full 4096 cap and ending `NameError`; riddles 7/14. One flag = 1.6 s vs 53 s per item.
- **Groot-19B-A3B (default arm):** pp 1876 / tg 78.2 / ttft 958 ms; preflight 3/3; needle 2k+8k PASS;
  riddles 8/14; HumanEval 0.9333 (56/60) at 15.6 s/item — **subset only, the full 164-item axis was
  never run (record as UNRANKED on the full axis)**; MMLU-Pro never run.
- vs the incumbent: gemma4-26b QAT is HE 0.9390 (164) / MMLU 0.8417 (120) / riddles 14/14 at 66.7 t/s.

### Restore recipe
- `sage-a1.5-Q4_K_M.gguf` — 21,713,463,520 B (20.22 GiB), sha256 `a64fe0bbf936db3eb54f66f142c2b2eee569ade83673649f549a21daef8ca395`
  from `InternScience/Sage-A1.5-Q4_K_M-GGUF :: Sage-A1.5-Q4_K_M.gguf`
- `mmproj-Sage-A1.5.gguf` — 899,282,880 B (0.84 GiB), sha256 `51cd4410057e8dc4152ca771a726fbfb34856f047e7049018c757d42ddd481f2`
  from `InternScience/Sage-A1.5-Q4_K_M-GGUF :: Sage-A1.5-mmproj.gguf`
- `groot-19b-a3b-Q4_K_M.gguf` — 11,657,618,560 B (10.86 GiB), sha256 `0716cae1f19a39a786a463f7b8c068d50b3d7a74532fce73e5ea23ed98130796`
  from `GrootTeam/Groot-19B-A3B-261023-GGUF :: Groot-19B-A3B-261023-Q4_K_M.gguf`
- `mmproj-Groot-19B-A3B-BF16.gguf` — 902,822,016 B (0.84 GiB), sha256 `05a5c8a279b2589306824864d76d663063ba69ff1f399e6a283fae988fdff360`
  from `GrootTeam/Groot-19B-A3B-261023-GGUF :: mmproj-Groot-19B-A3B-261023-BF16.gguf`
- units `llama-sage-a15.service` (port **8183**, alias `sage-a1.5`) and `llama-groot-19b-a3b.service`
  (port **8189**, alias `groot-19b-a3b`); scripts `run-sage-a15.sh`, `run-groot-19b-a3b.sh`.
- arch `qwen35moe` for both (41 blocks; sage 256 experts top-8, groot 128 top-8; ctx_train 262144) —
  loads on the halo-box fork with no build. Vision needs the mmproj above (`--mmproj`), which loads
  as "loaded multimodal model" although this fork's `/props` exposes no `vision` key.
- flags: `-ngl 99 -c 131072 --flash-attn on --cache-type-k/v q8_0 --spec-type none -np 1 --jinja --metrics`;
  sage additionally `--chat-template-kwargs '{"enable_thinking":false}'` (see above — without it the
  model is unusable).
- artifacts: `~/llama-local/t20-sage-nothink-core.log`, `t20-sage-a1.5-core.log`, `t20-groot-19b-a3b-core.log`,
  `he-sage-full.log`, `he-sage-nothink.log`, `he-groot-19b-a3b.log`, `mmlu-sage-full.log`;
  `~/runs/` holds the t20 rows.

## ornith-122b-reap50 (REAP50 + UD-IQ2_XXS of Ornith-1.5-122B) — retired 2026-10-25, failed preflight

Fetched and tested on the user's instruction as the one candidate on the board that could improve the
roster (a quarter-size version of the box's #2 model). Rejected: it loops, and preflight catches it.

### Header (local peek, not the card)
- arch `qwen35moe`, **expert_count 128 vs the base 122B's 256**, 48 blocks vs 49, ctx_train 262144,
  32 q / 2 kv heads. Genuinely pruned, not a rename.

### Measured on the halo-box fork, ctx 32768, q8_0 KV, flags mirrored from run-ornith-122b.sh
- perf: **pp 604 t/s · tg 37.2 t/s · ttft 2976 ms** @1797-token prompt — 1.6x the base 122B's 23.3 t/s
  at ~15 GiB resident instead of ~74 GiB.
- preflight **1/3**: content_nonempty PASS; `json_schema` FAIL (emitted the identical JSON blob four
  times back to back); `instruction_one_word` FAIL (argued with itself about whether a trailing period
  counts as part of the word).
- needle 2k PASS and 8k PASS, but both replies echo the needle repeatedly with stray `</think>` fragments.
- riddles: **aborted with 0 items scored** — the first item did not finish inside five minutes.
- **HumanEval and MMLU-Pro were never obtained** (the run was stopped after preflight failed). Their
  absence is deliberate, not a gap: do not read this model as having a code score.
- The repo's own `eval/summary.json` claims HE 0.9390 (154/164) and MBPP 0.8042 vs base 0.9451 / 0.8095,
  measured **reasoning on, cap 32768, temp 0.6, parallel 8** — a protocol that flatters a looping model
  and is not comparable to the t20 cells here (cap 4096, temp 0).

### Restore recipe
- `ornith-122b-reap50-IQ2_XXS.gguf` — 21,415,883,744 B (19.95 GiB), sha256 `6c0e926ef3f8f963555927aea5937a72fb1d737d33de58e4d6ed46fcaf2da739`
  from `anik-jha/Ornith-1.5-122B-24GB-GGUF :: Ornith-1.5-122B-24GB-REAP50-UD-IQ2_XXS.gguf`
- unit `llama-ornith-122b-reap50.service`, port **8183** (free again), alias `ornith-122b-reap50`,
  script `run-ornith-122b-reap50.sh`:
  `-ngl 99 -c 32768 --flash-attn on --cache-type-k/v q8_0 -np 1 --jinja --metrics`
- **TEXT ONLY** — the repo ships no mmproj, unlike the base 122B.
- artifacts: `~/llama-local/t20-reap50-core.log`, `test-reap50.out`, `ornith-122b-reap50.log`.


## raon-1-mini-preview (KRAFTON, hybrid MoE) — tested and retired 2026-10-26

Fetched and fully measured on the user's instruction ("get and test 1,2 and 3"). Rejected on quality:
it lands on mellum21-fork's HumanEval but loses on knowledge and riddles, and is slower than the
deployed driver on every axis.

### What it is
- 128 routed experts, 25 blocks, hidden 2560, 18 linear-attention + 7 full-attention layers,
  ctx 262144, arch `raon1_mini` / `Raon1MiniForCausalLM`.
- **Requires KRAFTON's fork**: `LLM_ARCH_RAON1` exists in github.com/krafton-ai/llama.cpp and
  nowhere else — not in our fork, not in prism, not in ggml-org master, no open PR. Upstream
  support "pending" per their own model card. Read this as a standing maintenance cost: any other
  work on our fork does not carry this arch.
- Their repo ships one extra file, `dflash-raon-1-mini-preview-Q8_0.gguf` (0.68 GiB), unused here.

### Measured (KRAFTON fork, ctx 32768, q8_0 KV, -ngl 99, flash-attn on)
- perf: pp 515 t/s · **tg 46.9 t/s alone** (19.5 t/s measured concurrently with another bench —
  always re-measure alone) · ttft 2108 ms @1086-token prompt.
- preflight **3/3 PASS**; needle 2k PASS, 8k PASS.
- HumanEval **0.9146 (150/164)**, 17.6 s/item, wall 2878 s.
- MMLU-Pro **0.7750 (93/120)**, 24.7 s/item, **17 cap-burns** (4% of items returned empty after
  burning the full 4096).
- riddles **8/14** — three failures were empty/cap-burn, two genuinely wrong (including a
  reverse-alphabet item where it wrote out the substitution correctly and still mis-decoded it).
- Verdict vs driver (gemma4-26b-a4b QAT): HE -2.4 pp, MMLU -6.7 pp, riddles 8 vs 14, and 46.9 vs
  59.5-66.7 t/s. No seat.
- Thinking stays in `reasoning_content` and is short (~25 tokens), which is why it is efficient per
  item despite being weaker — a template that other thinking models on this box should copy.

### Restore recipe
- `raon-1-mini-preview-IQ4_XS.gguf` — 16,071,801,344 B (14.97 GiB),
  sha256 `85570a704f9adc0df8b5b64c4e74ce956a5519e4868636d5daa00a84eb30696f`
  from `KRAFTON/Raon-1-mini-preview-gguf` (also Q4_K_M 18.33, Q5_K_M 20.66, Q6_K 24.06, Q8_0 28.59)
- build: `~/llama-local/krafton-llama.cpp` (cloned, Vulkan-built, 15,976-byte llama-server)
- serve: `~/llama-local/run-raon-1-mini.sh` (port 8181, alias `raon-1-mini`)
- bench: `~/llama-local/bench-raon.sh`; logs `t20-raon-core.log`, `he-raon.log`, `mmlu-raon.log`

## spark-x26-4b (XHToken, 4B dense, 1M ctx) — tested and retired 2026-10-26

Fetched because a 4B with a 1,048,576-token context was the only cheap way to fill a fast
long-context lane. The context is real; the model is not good enough to serve.

### What it is
- 4B dense, 36 blocks, hidden 2560, 16 heads / 4 kv (`spark2_5.block_count`), declared
  `context_length` 1048576. Loader: **`LLM_ARCH_SPARK2_5` already present in our fork and in
  upstream master** — no rebuild needed, which made it the cheapest of the three to test.

### Measured (fork, q8_0 KV, -np 1)
- perf: **pp 2263 t/s @1857-token prompt · tg 60.7 t/s · ttft 820 ms**.
- At long context prefill collapses: **455 t/s at 234,720 prompt tokens** (a full 1M prompt would
  take ~37 minutes).
- preflight **3/3 PASS**; needle 2k PASS, 8k PASS.
- HumanEval **0.6833 (41/60)** on a 60-item subset, 36.0 s/item — **17 of 60 items burned the full
  4096 cap and returned empty**. The score understates capability, but it is what an agent gets at
  a realistic cap; the subset carries ~3.5 pp standard error.
- MMLU-Pro **abandoned**: 9 items in 20 minutes, 3 pass, near-every item cap-burning. Do not read
  this as a measurement gap — run it only if someone first fixes the cap-burn behaviour.
- IFEval **not run**: there is no standalone `~/bench/ifeval.py`; IFEval on this box is an lm-eval
  task, and the archive's column comes from that path.
- riddles **10/14** (three of the four failures were empty/cap-burn).
- context: loads at a true n_ctx 1048576 with ~20 GiB of KV (GTT 35.5 -> 55.5 GiB), and retrieved a
  planted passphrase at 234,720 tokens in 515 s. Live but not useful at that cost, with
  Kimi-Linear already holding the long-context lane.

### Restore recipe
- `spark-x26-4b-Q4_K_M.gguf` — 3,543,441,312 B (3.30 GiB),
  sha256 `91cb2811aebb47ac916aa619d27d4cdd7f4143106b7917accb8ead4cd7f5cbd9`
  from `XHToken/Spark-X2.6-4B-GGUF` (also Q8_0 4.07 GiB, BF16 7.66 GiB)
- serve: `~/llama-local/run-spark-x26-4b.sh` (port 8180, -c 65536) or `run-spark-1m.sh` (-c 1048576)
- bench: `bench-spark.sh` / `bench-spark2.sh`; long-context: `needle-long.py <port> <tokens>`
- logs: `t20-spark-core.log`, `he-spark60.log`, `mmlu-spark60.log`, `needle-200k.log`

## sensenova-u15-8b-mot (SenseNova U1.5 8B MoT) — NOT RUNNABLE, deleted 2026-10-26

Never ran, and no amount of local work changes that without upstream effort.

- Every public GGUF for this model (`realrebelai/SenseNova-U1.5-8B_GGUFs`,
  `smthem/SenseNova-U1-8B-MoT-Merger-gguf`) declares **`general.architecture = wan`** with only 4
  metadata keys and tensors named `fm_modules.vision_model_mot_gen.*`,
  `fm_modules.noise_scale_embedder.*`, `patch_embedding.*`. That is **Wan video-diffusion
  packaging**, not an autoregressive LLM. The loader rejects it before anything else with
  `tensor name 1 is too long: 65 >= 64`, which is a red herring: even reading the names shows it is
  the wrong architecture.
- ggml-org master registers `LLM_ARCH_SENSENOVA_U1` (merged 2026-10-21, PR #28919) and has a
  `llama_model_sensenova_u1` class, but **`convert_hf_to_gguf.py` has no sensenova or wan
  converter** — so the official 32.7 GiB safetensors cannot be turned into a loadable GGUF here.
  Testing it means writing a converter first.
- Deleted: `sensenova-u15-8b-mot-Q5_K_M.gguf` — 15,107,169,664 B (14.07 GiB),
  sha256 `1c496256eb114a5ff8fef278a63b39a75bd0c36e76f4280e89a06bb6ecb76ade`.
- Kept: `~/llama-local/sensenova-llama.cpp` (upstream master, Vulkan-built) for when a converter
  appears.
- **General lesson: check `general.architecture` in a GGUF header before downloading anything big.**
  A repo named "*-GGUF" under a model's name can still be diffusion weights for ComfyUI. One
  `head -c 4M` + header read costs seconds; the Q5 file here cost 14 GiB and an hour.

## nanbeige-33b (Nanbeige4.3-33B Q4_K_M) — measured, dominated, deleted 2026-10-26

Fetched at the user's request, measured on all axes, then retired on "retire and delete". Not a
broken model — clean preflight 3/3, both needles PASS, zero MMLU cap burns — it simply loses to
models already on disk.

Measured (bartowski imatrix Q4_K_M, 19.36 GiB, fork Vulkan, :8183, `-c 32768`, q8_0 KV, cap 4096):

    HumanEval   0.8963 (147/164)   169 min, 62.0 s/item, mean 640 tok, 9 cap burns
    MMLU-Pro    0.7167 ( 86/120)    53 min, 26.5 s/item, mean 270 tok, 0 cap burns
    riddles     13/14 · preflight 3/3 · needle 2k+8k PASS
    perf        pp 352.1 t/s · tg 10.4 t/s · ttft 5.19 s  (dense 33B, bandwidth-bound)

Why it went: gemma4-31b is the same size class and scores +6.7 pp HumanEval, +15.0 pp MMLU-Pro,
14/14 riddles, and decodes 1.6x faster; the gemma4-26b-qat driver beats it on all three while
running ~6x faster. Decode at 10.4 t/s is the bandwidth law for 19.4 GB read per token, so no
tuning recovers it. Ranks 14/26 HumanEval, 11/25 MMLU-Pro, last of 26 on decode.

What was removed:

    ~/llama-local/models/Nanbeige_Nanbeige4.3-33B-Q4_K_M.gguf   20,788,825,216 B (19.36 GiB)
    ~/llama-local/models/.cache/huggingface/                    hf download staging
    ~/llama-local/run-nanbeige-33b.sh                           the unit's ExecStart
    ~/.config/systemd/user/llama-nanbeige-33b.service
    llama-switch entry `nanbeige-33b` (:8183) + its usage string
    llama-nanbeige-33b.service from every other unit's Conflicts= line
    transient bench units bench-nanbeige, bench-nanbeige-he

Restore:

    cd ~/llama-local/models && wget -c \
      https://huggingface.co/bartowski/Nanbeige_Nanbeige4.3-33B-GGUF/resolve/main/Nanbeige_Nanbeige4.3-33B-Q4_K_M.gguf
    # expected 20,788,825,216 B,
    # sha256 2cef79855ca47ee6571e166db32a07089e34f3cf78e0397b262d124ddb814c37

    # then recreate the unit; the flags that matter are the plain ones — arch is `llama`, so the
    # stock fork loads it with no special build:
    #   --port 8183 -ngl 99 -c 32768 --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0
    #   --jinja --reasoning off -np 1 -b 4096 -ub 2048 --metrics
    # (no MTP/drafter ships for this base; there is no spec-decode arm)

- Note for a future uncensored run: `dealignai/Nanbeige4.3-33B-UNCENSORED-GGUF` (Q4_K_M 18.7 GiB)
  exists and was NOT tested. It inherits this model's speed class (~10 t/s dense), so judge it only
  as a §16 abliteration datapoint, not as a daily driver.
- Measurement hygiene found while ranking: three catalogue rows `20261010-17*` carry HumanEval 1.000
  and MMLU 1.000 for qwen3next-q6 at **n=2** — assertion smoke tests, not measurements. Filter on
  `humaneval_n >= 50` before ranking, or they sit at the top of every table.

# ————— Pruning pass 2026-10-30 (retire and delete, record kept) —————

Eight artefacts retired, 245.1 GiB. Two further candidates were HELD mid-pass
(NVIDIA-Nemotron-3.5-Super-VL-120B, LFM2.5-24B-A2B): the numbers I proposed them on were cap-demoted,
and at cap 4096 both read far better than quoted. See the last section.

## Swift-Qwen3.8-Flash-Next-GSQ-RCO IQ2_XS (abliterated v2, huihui-ai) — retired 2026-10-30  [T1, 63.5 GiB]

Why it went: Capability never measured — both runs on it are perf-only, so there is no HumanEval or MMLU-Pro row for this exact file. It is a second, lower-quant encoding of the model :8097 already serves as IQ3_S (which is protected), so nothing on the box loses a capability.

Measured:

    perf        tg 31.2-31.5 t/s (20261027-111946-flashnext-smoke, 20261027-112508-flashnext-abl, :8190)
    riddles     13/14 · HumanEval none · MMLU-Pro none
    header      qwen4exp arch, 48 layers, 512 experts, ~4B active, 262144 ctx, ftype IQ2_XS 2.3125 bpw

What was removed:

    ~/llama-local/run-qwen38-flash-next-abl.sh
    ~/llama-local/models/qwen38-flash-next/  (whole tree incl .cache/huggingface staging)

Files and hashes (sha256 taken immediately before deletion):

    ~/llama-local/models/qwen38-flash-next/.cache/huggingface/trees/411f1f7349c9711e6f75aa8d20e1612eb3a4d55d.json   13,973 B (0.00 GiB)
    ~/llama-local/models/qwen38-flash-next/swift-IQ2_XS/Swift-Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00001-of-00002.gguf   39,788,473,344 B (37.06 GiB)
      sha256 514a369bff816ed78f23e0054688b570eae538299ccae45173908b5a69e468c9
    ~/llama-local/models/qwen38-flash-next/swift-IQ2_XS/Swift-Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00002-of-00002.gguf   28,363,693,824 B (26.42 GiB)
      sha256 9ffb75cdd312d669bc783b4d861d587f9553ab678fbc6963765ffde6b2728234

Restore:

    # publisher repo (huihui-ai) is named in the script header, but the published file basename
    # lacks the "Swift-" prefix this copy carries, so restore by HASH not by name:
    #   Swift-...-00001 68d...  see the sha256 lines above; llama.cpp fork build b3-1a33095 needed
    #   (qwen4exp arch), -c 16384 on purpose: 63.5 GiB + driver overflows a 100 GiB pool.

## Huihui-Qwen3.8-27B-Coder390-EfficientThink-abliterated IQ3_S1 — retired 2026-10-30  [T1, 11.3 GiB]

Why it went: Dense 27B (fails the standing shape rule) with no capability row at all: the only run is a perf probe. Measured 16.3 t/s, which is the bandwidth law for a dense 27B on this box and not a tuning problem. The script header itself says IQ3_S is aggressive for a coder, so it was never a fair test of the model — only of this file.

Measured:

    perf        tg 16.3 t/s (20261027-012115-coder390, :8183)
    HumanEval none · MMLU-Pro none · riddles 14/14
    header      dense 65 layers, 24 heads, 4 kv heads, head_dim 256

What was removed:

    ~/llama-local/run-coder390-abl.sh
    ~/llama-local/models/coder390/  (whole tree incl .cache/huggingface staging)

Files and hashes (sha256 taken immediately before deletion):

    ~/llama-local/models/coder390/Huihui-Qwen3.8-27B-Coder390-EfficientThink-abliterated-IQ3_S1.gguf   12,143,609,632 B (11.31 GiB)
      sha256 8c5d471ff4b5e26d1fc6c53fffef8fa9f09b441b0fd4425baec42ff9567b0df5

Restore:

    cd ~/llama-local/models && wget -c \
      https://huggingface.co/huihui-ai/Huihui-Qwen3.8-27B-Coder390-EfficientThink-abliterated-GGUF/resolve/main/Huihui-Qwen3.8-27B-Coder390-EfficientThink-abliterated-IQ3_S1.gguf
    # expected 12,143,609,632 B, sha256 8c5d471ff4b5e26d1fc6c53fffef8fa9f09b441b0fd4425baec42ff9567b0df5 (= repo LFS oid, verified)
    # if retried, use a higher quant: the repo publishes IQ4_XS and up, and only then is a HE number about the model.

## NVIDIA-Nemotron-3.5-Bolt-E4B UD-Q8_K_XL — retired 2026-10-30  [T1, 8.9 GiB]

Why it went: Never measured: no run ever attached to its port (8187 was reused by other scratch models), so there is no perf and no capability row. Its unit was disabled and it is not referenced by any script that survives.

Measured:

    no rows at all in ~/runs (120 run files checked by port and by id)
    header      dense-ish 42 layers (Mamba hybrid), 8 heads, head_dim 512, ftype UD-Q8_K_XL

What was removed:

    ~/llama-local/run-nemotron-bolt-e4b.sh
    ~/llama-local/models/dflash-NVIDIA-Nemotron-3.5-Bolt-E4B-Q8_0.gguf   (its drafter)
    ~/llama-local/models/mmproj-NVIDIA-Nemotron-3.5-Bolt-E4B-F16.gguf   (its projector)
    ~/.config/systemd/user/llama-nemotron-bolt-e4b.service

Files and hashes (sha256 taken immediately before deletion):

    ~/llama-local/models/NVIDIA-Nemotron-3.5-Bolt-E4B-UD-Q8_K_XL.gguf   8,192,955,584 B (7.63 GiB)
      sha256 6176bd788769bd58042c165d3dc8e8c86a8ca5c90d5de188a364b31dc9560810
    ~/llama-local/models/dflash-NVIDIA-Nemotron-3.5-Bolt-E4B-Q8_0.gguf   398,892,256 B (0.37 GiB)
      sha256 9a63662ae8395b8bfc1a1b00d7a9ef354120f172704bd6ba88d3870cf22d4d03
    ~/llama-local/models/mmproj-NVIDIA-Nemotron-3.5-Bolt-E4B-F16.gguf   990,373,568 B (0.92 GiB)
      sha256 6bc77b7ac2b62cf61bc86757605e45e39f6345373f0a6b76cc5b1ed97f2e233e

Restore:

    # repo nvidia/NVIDIA-Nemotron-3.5-Bolt-E4B-GGUF, UD-Q8_K_XL + drafter + mmproj;
    # verify against the sha256 lines above. Arch needs the fork build; -ngl 99, dflash spec-type.

## gemma-4-26B-A4B-it Q8_0 — RETIRED, but its row was genuine — retired 2026-10-30  [T2, 26.1 GiB]

Why it went: Duplicate quant of a family that already has two better-value files on disk. Re-measured 2026-10-30 specifically to settle a suspicion that its Oct 17 baseline row had borrowed the driver numbers: it had not — it reproduces item-for-item — so this is a SIZE/SPEED decision, not a distrust decision. Q8 157/164 + 104/120 @2048 at 49.4 t/s and 26.1 GiB versus the uncen Q4_K_M 157/164 + 102/120 at 56.9 t/s and 15.6 GiB, i.e. +10.5 GiB and -8 t/s for 2 items (1.7 pp against a 3.3 pp SE = noise).

Measured:

    20261030-045147-gemma-q8-remeasure  HE 0.9573 (157/164)  MMLU 0.8667 (104/120)  both @2048  tg 49.4  riddles 14/14
    20261017-140527-gemma-q8-baseline   HE 0.9573 (157/164)  MMLU 0.8500 (102/120)  both @2048  tg 41.6
    header      gemma4 arch, MoE 30 layers, 16 heads, head_dim 512, 25,233,142,046 params

What was removed:

    ~/llama-local/run-gemma4-26b-a4b-q8.sh
    ~/llama-local/models/gemma-4-26B-A4B-it-Q8_0.gguf  (+ its -sha256.txt)
    ~/llama-local/models/mmproj-gemma4-26B-A4B-F16.gguf  (+ its -sha256.txt)
    # the MTP drafter mtp-gemma-4-26B-A4B-it-Q8_0.gguf STAYS — the QAT driver loads it.

Files and hashes (sha256 taken immediately before deletion):

    ~/llama-local/models/gemma-4-26B-A4B-it-Q8_0.gguf   26,859,861,728 B (25.02 GiB)
      sha256 5f7cbd0f4564e84342fc34321a09acb54b1a3da9215124e5bf444baa6dda152c
    ~/llama-local/models/mmproj-gemma4-26B-A4B-F16.gguf   1,193,058,784 B (1.11 GiB)
      sha256 418a6d8723067cd712235facbbc5cba6c8fbbd413fc1292d2aace5a027d5a42f

Restore:

    cd ~/llama-local/models && wget -c \
      https://huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF/resolve/main/gemma-4-26B-A4B-it-Q8_0.gguf
    # expected 26,859,861,728 B, sha256 5f7cbd0f4564e84342fc34321a09acb54b1a3da9215124e5bf444baa6dda152c (= repo LFS oid, verified)
    # projector from the same repo (mmproj-F16.gguf); serve with -c 131072, q8_0 KV, --reasoning off.

## Ling-3.0-flash Q4_K_M (inclusionAI) — retired 2026-10-30  [T3, 71.7 GiB]

Why it went: 71.7 GiB — the second-largest artefact on the box — for a single measured axis. MMLU-Pro 0.7667 is respectable; HumanEval was never run, so the code axis is unknown, and it takes the whole 100 GiB pool to itself (77 GB weights + KV), meaning serving it silences the driver and the WhatsApp channel.

Measured:

    20261022-231115-ling3-flash-core   MMLU 0.7667 (92/120) @2048   HumanEval none   tg 43.5 t/s   riddles 11/14
    header      bailingmoe3 arch, 43 layers, 512 experts / 8 per token, 262144 ctx, MIT

What was removed:

    ~/llama-local/run-ling3-flash.sh
    ~/llama-local/models/Ling-3.0-flash-Q4_K_M/  (2 shards)

Files and hashes (sha256 taken immediately before deletion):

    ~/llama-local/models/Ling-3.0-flash-Q4_K_M/Ling-3.0-flash-Q4_K_M-00001-of-00002.gguf   49,995,534,208 B (46.56 GiB)
      sha256 24ff06f1ab74546a91f7c07bd725b3015896bbe9dd82ab0e5838be9ed06a6dcf
    ~/llama-local/models/Ling-3.0-flash-Q4_K_M/Ling-3.0-flash-Q4_K_M-00002-of-00002.gguf   27,014,610,464 B (25.16 GiB)
      sha256 1a6a8c91562b817fd8ec5b250453be696b0fc209ed8f2acdb6c13f4e17f7e188

Restore:

    # publisher: inclusionAI/Ling-3.0-flash. The exact GGUF repo was never recorded in the script
    # header and that org does not expose a -GGUF repo with these shard names, so restore by hash:
    #   shard 1 24ff06f1ab74546a91f7c07bd725b3015896bbe9dd82ab0e5838be9ed06a6dcf
    #   shard 2 1a6a8c91562b817fd8ec5b250453be696b0fc209ed8f2acdb6c13f4e17f7e188
    # arch bailingmoe3 is in the fork tree; -c 131072 needs the pool to itself.

## NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB IQ2_XXS — retired 2026-10-30  [T3, 23.1 GiB]

Why it went: The one genuinely split result on the box: HumanEval 0.945 (155/164) but MMLU-Pro 0.367 (44/120) @2048 — it codes and does not know. At 2.0625 bpw the quant is also the most damaged artifact here, and the knowledge axis is the one that cannot be recovered by a bigger cap (the 4096 arms do not exist for this file).

Measured:

    20261016-095244-placement   HE 0.9451 (155/164)  MMLU 0.3667 (44/120)  both @2048  tg 72.8  riddles 13/14
    20261016-092339             tg 74.3 (perf only)
    20261030-034330-bolt74b-core tg 69.4, riddles 14/14
    header      nemotron_h MoE 88 layers, 32 heads, head_dim 128, ftype IQ2_XXS 2.0625 bpw

What was removed:

    ~/llama-local/run-nemotron-bolt.sh, run-nemotron-bolt-74b-fork.sh, run-nemotron-bolt-74b-think.sh, fetch-nemotron-bolt.sh
    ~/llama-local/models/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB.gguf  (+ -sha256.txt)
    ~/llama-local/models/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB-LiLiCorr.gguf  (its dflash drafter, + -sha256.txt)
    ~/llama-local/models/mmproj-NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB.gguf  (+ -sha256.txt)
    ~/.config/systemd/user/llama-nemotron-bolt-74b.service

Files and hashes (sha256 taken immediately before deletion):

    ~/llama-local/models/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB.gguf   22,018,326,528 B (20.51 GiB)
      sha256 91d63363e782c8a3d5f4be42816eba8e0d42dd2530bd07a7d0d2dc440599af75
    ~/llama-local/models/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB-LiLiCorr.gguf   998,242,560 B (0.93 GiB)
      sha256 080e1ea41c9562a7804dbf30c6fbd4d17e216c6b8ff666f88e6edb1816010194
    ~/llama-local/models/mmproj-NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB.gguf   1,733,692,736 B (1.61 GiB)
      sha256 0ee891eadc7bf0cae6289b249c74eb1ef420534351f6ef8b64d49f0ca6a926b0

Restore:

    cd ~/llama-local/models && wget -c \
      https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB-GGUF/resolve/main/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB.gguf
    # expected 22,018,326,528 B, sha256 91d63363e782c8a3d5f4be42816eba8e0d42dd2530bd07a7d0d2dc440599af75 (= repo LFS oid, verified)
    # drafter: nvidia/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB-LiLiCorr-GGUF, mmproj from the main repo.
    # if re-fetched, take a HIGHER quant: the MMLU 0.367 is the 2-bit floor, not the model.

## Flint-40B-A2.5B-abliterated i1-Q4_K_M (mradermacher) — retired 2026-10-30  [T1, 22.5 GiB]

Why it went: No capability row attributable to THIS file. Its provenance is the abliterated derivative of dima6312/Flint-40B-A2.5B-abliterated, re-quantised by mradermacher — the 123/164 + 62/120 numbers that appear under the run alias "flint" belong to the earlier, differently-named FLINT artefact (RecursiveSI publisher UD-Q4_K_XL), which was itself retired on 2026-10-24. All this file has is a 60-item HumanEval probe at cap 4096 (55/60 = 0.9167) and no MMLU at all, so nothing about its knowledge axis is known and 22.5 GiB buys an unmeasured duplicate of a retired family.

Measured:

    20261025-070907-flint-q4-he60   HE 55/60 (0.9167) @4096 — a 60-item probe, not a full axis; MMLU none
    20261027-165746-flint40b-abl, 20261027-170747-flint40b-abl-8k   perf only, tg 70.8-71.1 t/s, riddles 10/14
    header      flint arch, MoE 49 layers, 256 experts / 2 shared, 4 kv heads, 262144 ctx, sliding window
    NOT QUOTABLE: the 123/164 @2048 and 62/120 @2048 under run alias "flint" (20261021-210703) are the other file.

What was removed:

    ~/llama-local/run-flint40b-abl.sh
    ~/llama-local/models/Flint-40B-A2.5B-abliterated.i1-Q4_K_M.gguf

Files and hashes (sha256 taken immediately before deletion):

    ~/llama-local/models/Flint-40B-A2.5B-abliterated.i1-Q4_K_M.gguf   24,166,842,912 B (22.51 GiB)
      sha256 a7f6f33bbef675e3f243123d22af35667d6063515fd2c71bb122083d73395178

Restore:

    # dima6312/Flint-40B-A2.5B-abliterated-GGUF (publisher quant, 24,166,842,272 B,
    # sha256 5ac7c931803a9fff117c5cde1cda6b7bd840f5678b28a31cfe77870e9c201cf7) or
    # mradermacher/Flint-40B-A2.5B-abliterated-GGUF (imatrix re-quant, 24,166,842,656 B,
    # sha256 25ab4aee8a3fe5e55de4cec8f6a33c58263bcb876e9121ab0c57aa725403238f).
    # The retired local file was 24,166,842,912 B with its own hash (see above) — near but not equal
    # to either, so restore by hash or accept a different file.
    # arch flint is NOT in the halo-box fork: it needs ~/llama-local/flint-llama.cpp (upstream master, PR #30928).

## gemma-4-31B-it QAT Q4_0 (DENSE) — retired 2026-10-30  [T3, 18.0 GiB]

Why it went: Best HumanEval on the box (158/164 = 0.9634) and equal-best MMLU-Pro, and still the right thing to drop: it is DENSE, which is out of scope by the standing rule, and 17.0 t/s makes it the slowest useful model here — a suite run on it costs ~2.5x the wall clock of any MoE at the same score. Losing the top HE row is also the honest outcome: the 26B-A4B Q8 posts 157/164 at 49 t/s and the uncen Q4_K_M 157/164 at 57 t/s, i.e. one item for 3x the decode speed.

Measured:

    20261021-115453-gemma4-31b-full   HE 0.9634 (158/164)  MMLU 0.8667 (104/120)  both @2048  tg 17.0  riddles 14/14
    20261021-115218-gemma4-31b        tg 17.2, riddles 14/14
    header      gemma4 arch, DENSE 60 layers, 32 heads, head_dim 512 (global), vocab 262144

What was removed:

    ~/llama-local/run-gemma4-31b.sh
    ~/llama-local/models/gemma-4-31B_q4_0-it.gguf
    ~/llama-local/models/mtp-gemma-4-31B-it-Q8_0.gguf        (its MTP drafter)
    ~/llama-local/models/mmproj-gemma4-31B-QAT.gguf          (its projector)
    ~/.config/systemd/user/llama-gemma4-31b.service

Files and hashes (sha256 taken immediately before deletion):

    ~/llama-local/models/gemma-4-31B_q4_0-it.gguf   17,651,001,568 B (16.44 GiB)
      sha256 179cfb99212709597eae5929112cfca677e1bbf566178b479ae1da0c4772874b
    ~/llama-local/models/mtp-gemma-4-31B-it-Q8_0.gguf   514,705,920 B (0.48 GiB)
      sha256 e6e88dea4fcf79a0a71cd7732e61632355126dbbda9b72a08d6301fa06fbaf22
    ~/llama-local/models/mmproj-gemma4-31B-QAT.gguf   1,200,726,368 B (1.12 GiB)
      sha256 6bd60bdb958548b4093196d38744b0f2290c12503a3fddd7486bffa9c5eb07a4

Restore:

    cd ~/llama-local/models && wget -c \
      https://huggingface.co/google/gemma-4-31B-it-qat-q4_0-gguf/resolve/main/gemma-4-31B_q4_0-it.gguf
    # expected 17,651,001,568 B, sha256 179cfb99212709597eae5929112cfca677e1bbf566178b479ae1da0c4772874b
    # (unsloth mirror: unsloth/gemma-4-31B-it-qat-GGUF). KV is cheap: 50 of 60 layers are sliding-window 1024.

## HELD — not deleted in this pass

**NVIDIA-Nemotron-3.5-Super-VL-120B-A12B UD-Q3_K_XL (62.9 GiB)** — I proposed it on HE 137/164 and
MMLU 80/120, which are the @2048 numbers. The cap-4096 arms exist and are much better:
`20261018-063326` HE 156/164 + MMLU 91/120 @4096, `20261019-213244` HE 153/164 + MMLU 92/120 @4096,
tg 27.1. So it is mid-field, not weak — the case for deleting it is footprint only, and that needs a
deliberate call.

**LFM2.5-24B-A2B QAD-Q4_0 (13.3 GiB)** — same error: I quoted the @2048 pair (HE 73/164, MMLU 65/120)
when `20261017-002528-lfm25-cap4096` reads HE 140/164 (0.8537) + MMLU 83/120 (0.6917) @4096 at 106.6 t/s.
At that cap it is a strong small model, not a weak one.

Both are still on disk. Their hashes are in `retire-hashes.json` in the cache if a later pass needs them.

Lesson recorded for the next pruning pass: a score quoted without its cap understated these two by 12-19
pp; the run directory holds the 4096 arms, and `cap-arm.py` re-runs only the cap-pinned rows.

## Mistral-Small-4-119B-2603 (AtomicChat AD-IQ3_XXS) — fetched, measured, retired 2026-10-30

The one fit candidate of the 2026-10-30 sweep: 119B total, **6.5B active**, 36 layers, 128 routed
experts + 1 shared (top-4), MLA attention (kv_lora_rank 256 / qk_rope 64) so KV is 1.4 GiB at 128k,
native 1M ctx, base `mistralai/Mistral-Small-4-119B-2603`, apache-2.0.

**It loaded and served; it was the decode path that killed it.** arch `mistral4` is registered in
halo-box-strix-llama.cpp AND implemented — `llama_model_mistral4 : llama_model_deepseek2` reuses the
DeepSeek2 MLA graph and tensor loader, and every key that loader demands was present (q_lora_rank
1024, kv_lora_rank 256, expert_shared_count 1, expert_ff 2048, dense-lead 0; 36 layers misses
deepseek2's `is_lite` test, so it takes the full path). Served on :8086 with the driver still up at
**79.9 GiB of the 100 GiB pool** — it genuinely fits beside the channel.

Measured:

    perf (fork, b3-1a33095)   pp 424.8 t/s   tg 4.6 t/s   ttft 5.5 s
    perf (upstream-master-bolt) pp 296.7 t/s  tg 4.7-5.0 t/s   — same on both trees
    -ot "exps=Vulkan0"          tg 4.8 t/s   no change: the experts were not on CPU for placement reasons
    cores while decoding        ~10-12 of 16 busy, GPU 80% busy  → host-side MoE matmuls, the Mellum signature
    preflight                  3/3 PASS · needle 2k PASS · needle 8k PASS
    MMLU-Pro, 30-item probe    0.4000 (12/30) @512, every answer 2 tokens (bare letter, no deliberation)

Why it went: 4.8 t/s is a 6x miss against the 10B-active anchor class (~22 t/s), so a full suite would
have cost 6-8 hours and a chat channel would be unusable. The arch needs a Vulkan MUL_MAT_ID path for
this MLA+MoE graph (or a different implementation of `mistral4`); the quant is not the limiter — IQ3_S
on `qwen4exp` runs at 52.9 t/s on the same build. Revisit only if upstream adds that path.

What was removed:

    ~/llama-local/models/Mistral-Small-4-119B-2603/  (whole tree, 3 files, 47.03 GiB)
    ~/llama-local/run-mistral4-119b.sh, run-mistral4-119b-bolt.sh, run-mistral4-119b-ot.sh
    ~/llama-local/fetch-mistral4.py, mistral4.log, mistral4-bolt.log, mistral4-ot.log

Kept: the run rows — `~/runs/20261030-213551-mistral4-119b-core.jsonl` (identity + perf + preflight +
needle rows; the run was stopped before the riddles axis, so no riddles or capability row exists),
`~/runs/mistral4-core.out` (the same run's stdout) and `~/bench/runs/mmlupro-20261030-215224.jsonl`
(the 30 knowledge items).

Files and hashes (verified against the repo's LFS oids before deletion — all three MATCHED):

    Mistral-Small-4-119B-2603-AD-IQ3_XXS-00001-of-00002.gguf   44,675,271,232 B (41.61 GiB)
      sha256 eecc0ba10b0625cba7b84c174423c83127f8eeef55393ece734cdf02595aba93
    Mistral-Small-4-119B-2603-AD-IQ3_XXS-00002-of-00002.gguf    4,966,467,968 B ( 4.63 GiB)
      sha256 c32b5c36dce7efd5c5cc6fdab4c6faef1dafa4ec94aeb0bd1415d9cb6bc0e62a
    mmproj-Mistral-Small-4-119B-2603-F16.gguf                     857,078,016 B ( 0.80 GiB)
      sha256 f6fe6adda938b42073e256a582012d179f8c6b61361d5ca1f395b0fb6087bb53

Restore:

    mkdir -p ~/llama-local/models/Mistral-Small-4-119B-2603 && cd $_
    for f in "AD-IQ3_XXS/Mistral-Small-4-119B-2603-AD-IQ3_XXS-00001-of-00002.gguf" \
             "AD-IQ3_XXS/Mistral-Small-4-119B-2603-AD-IQ3_XXS-00002-of-00002.gguf" \
             "mmproj-Mistral-Small-4-119B-2603-F16.gguf"; do
      curl -sL -C - -O "https://huggingface.co/AtomicChat/Mistral-Small-4-119B-2603-GGUF/resolve/main/$f"
    done
    # flags that worked: -ngl 99 -c 131072 --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0
    #   --reasoning off -np 1 -b 4096 -ub 2048 --metrics   (mtmd has PIXTRAL but no MISTRAL projector
    #   type, so vision was never probed; add --mmproj only as a separate test)
    # If the IQ4_XS is ever tried: 64.5 GiB, needs the driver stopped, KL 0.0609 vs 0.1279 for this file.

## SandLogic Hy-Memory-30B-A3B Q4_K_M — retired 2026-10-29 (record backfilled)

Deleted in the 2026-10-29 pass (61.6 GiB batch: Kimi-Linear-48B-A3B, Hy-Memory-30B-A3B, Mellum2.1-12B
Q6_K and its MXFP4 twin). This section was written afterwards: that pass predates the rule that every
deletion is recorded *before* the files go, so **no sha256 was captured and the byte figure is the
17.0 GiB from the batch summary, not a measured stat**.

Measured — best run `20261017-110734-hy-memory-placement`:

    HumanEval   0.7805 (128/164 @ 2048)
    MMLU-Pro    0.7250 ( 87/120 @ 2048)
    riddles     12/14
    perf        pp 1514.6 t/s   tg 74.7 t/s

Why it went: 0.78 code is ordinary, and its one strength — 74.7 t/s — does not distinguish it.
`gptoss-abliterated` scores 0.9268 on code at 50 t/s for 59 GiB, and the 15.6 GiB gemma driver beats
it on both axes at 57 t/s. Nothing it did justified 17 GiB of resident space on a box that has to
choose.

Restore: upstream is `SandLogicTechnologies/Hy-Memory-30B-A3B`, Q4_K_M. There is no hash to verify
against, so verify by measuring: HumanEval should land near 0.78 at cap 2048 and decode near 74–75 t/s
on Vulkan. A materially different number means a different quant from the one that was tested.

## SandLogic Hy-Memory-30B-A3B Q8_0 — retired (record backfilled)

The Q8 arm of the same model, measured as the quant-ladder datapoint against the Q4_K_M above
(`20261017-124731-hy-memory-q8`):

    HumanEval   0.7683 (126/164 @ 2048)   ← −1.2 pp against Q4
    MMLU-Pro    0.7500 ( 90/120 @ 2048)   ← +2.5 pp against Q4
    riddles     11/14
    perf        pp 1459.2 t/s   tg 52.3 t/s   ← 30 % slower than Q4 for the extra bits

Deletion date, size and hashes were never recorded — the file left disk before the ledger rule
existed, so treat all three as unknown rather than reconstruct them. What survives is the run and the
delta, which is the useful part: doubling weight precision bought 2.5 pp of knowledge and cost 30 % of
decode speed, at identical caps. Expect roughly 32 GiB if it is ever restored from the same publisher.

## graft-50b-a3b (50.7B Q4_K_M) — retired (deletion record incomplete)

Measured 2026-10-19, run `20261019-122149-graft-50b-a3b`:

    HumanEval   0.7805 (128/164 @ 2048)
    MMLU-Pro    0.6583 ( 79/120 @ 2048)
    riddles     14/14     ← one of only seven 14/14 sweeps on this box
    perf        pp 1367.7 t/s   tg 54.3 t/s

This is the least complete entry in the ledger, and it says so deliberately: **no deletion date, no
byte count, no sha256 and no upstream repository were recorded before the file left disk.** The run
and the scores above are the only surviving evidence. It cannot be restored byte-for-byte — re-obtaining
it means identifying the publisher from the model name and re-measuring. If anyone does, the 14/14
riddle sweep is the number worth checking, because that is rarer on this box than a 0.78 HumanEval.

---

*Written with Hermes Agent (Nous Research) driven by DeepSeek's `deepseek-flash`, from the run archive
and from the sha256 values taken immediately before each deletion. Where a hash or date was never
captured, the entry says so rather than filling the gap.*

## Apexintelligence-AI Apex-35B-V1.0 Q4_K_M (bartowski) — retired 2026-11-01

**Rejected on evidence, not on size.** Fetched 2026-11-01 11:47 → 12:06 (21.23 GiB at 40 MB/s), tested
the same afternoon, deleted the same afternoon.

### Why

The finetune does not terminate its reasoning on this build. Riddle items return `completion_n` equal to
the cap with an **empty `content`** — the model thinks until the budget is gone and never answers:

| cap | riddles | items that burned the whole cap with no answer |
|---|---|---|
| 4096 | 9/14 | 5 of 14 (n=4096, content empty) |
| 8192 | 9/14 | 3 of 14 (n=8192, content empty) |

HumanEval tells the same story at 0.4146 (68/164) with a 2203 s wall — 13.4 s/item at 61 t/s, i.e. ~800
tokens of thinking per item and zero credit when it runs out. MMLU-Pro with thinking forced off reached
0.5800 (58/100). At the same 35B-A3B shape this roster carries qwen38-35b at 0.8720/0.6417 and
Ornith-1.5-35B at 0.8354/0.4417, so the model is outside the band even before the non-termination.

### Measured rows

| run | axes | result |
|---|---|---|
| `20261101-124818-apex35b-cap4096` | HE 164, riddles, perf, preflight, needles | HE 0.4146 (68/164) 2203 s; riddles 9/14; pp 1991.7 / tg 61.5 / ttft 902 ms; preflight 3/3; needles 2k+8k PASS |
| `20261101-133139-apex35b-cap8192-probe` | core at cap 8192 | riddles 9/14; pp 2005.5 / tg 60.1 / ttft 896 ms; preflight 3/3; needles PASS |

### Removed

| path | bytes | sha256 |
|---|---:|---|
| `models/Apexintelligence-AI_Apex-35B-V1.0-Q4_K_M.gguf` | 22,795,471,072 | `c1bf4a6008bda54c6da3be1e5b6137a9b31cbe7d5a5432950215b0d13da2296b` |
| `run-apex-35b.sh`, `run-apex-35b-bench.sh`, `apex-bench.log` | small | — |

### Restore

`hf` / `bartowski/Apexintelligence-AI_Apex-35B-V1.0-GGUF` → `Apexintelligence-AI_Apex-35B-V1.0-Q4_K_M.gguf`,
expect 22,795,471,072 bytes and the sha256 above. Re-download only to study the template — the harness
(`t20`) and a `--jinja` server were not the problem, and a reasoning-effort cap did not fix it either.

---

*Source: [github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io](https://github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io). Entries written after 2026-10-30 record the sha256 before deleting; earlier ones say when a hash was never captured.*
