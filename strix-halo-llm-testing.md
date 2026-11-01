# Testing Local LLMs on AMD Strix Halo
> **Also published:** [Retired models — what was deleted, why, with hashes and restore recipes](retired-models.html).


**Why this rig exists, how it is measured, what the numbers mean, and which model to pick for what**

- **Host:** Minisforum **MS-S1 MAX** (product_family `MINISFORUM`, board `SHWSA`, BIOS 1.06, EC 0.15)
  · OS: CachyOS Linux · GPU: Radeon 8060S (Strix Halo, gfx1151)
- **Runtime:** llama.cpp on Vulkan · **Harness:** `~/bench` (`t20`)
- **Archive:** `~/runs/catalogue.json` · **Measurements:** 2026-10-07 → 2026-10-31
- **Roster:** 16 servable artefacts on disk, 602 GiB, checked 2026-10-31 · **Change log:** §21

**About this document**

*Audience:* someone deciding what to run on a 128 GB unified-memory AMD machine, and someone
checking whether the numbers are honest. *Provenance:* every figure comes from a run recorded in
`~/runs/catalogue.json`, a log file, or a query against the hardware monitor's database; nothing is
quoted from a vendor or a leaderboard. *What it is not:* a benchmark of these models in general. It
is a measurement of one machine, at one software version, at stated caps — §10.5 and §14.6 say
exactly how far that can be pushed.

**Contents**

```
   0   Executive summary                seven claims that frame everything
   1   Why test at all                  four reasons leaderboards fail on this hardware
   2   The platform                     silicon, memory topology, active-parameter arithmetic
   3   The OS and driver stack          CachyOS / kernel / Mesa / RADV; Vulkan rather than ROCm
   4   The runtime                      three llama.cpp trees, build flags, the commit behind each
   5   Memory and quantisation          GTT, KV accounting, the quant ladder, its failure modes
   6   The serving architecture         exclusive units, the availability guard, bench isolation
   7   The harness                      seven axes, one test per axis, the cap, artefacts
   8   How to read the results          five rules of interpretation
   9   Results                          the measured matrix and a verdict per model
  10   Extrapolation                    whether a family result transfers, and what cannot
  11   League tables                    per-axis rankings
  12   Which model for which job        job -> axis -> model, with anti-patterns
  13   Strix Halo vs Nvidia vs Apple    capacity, bandwidth, ecosystem, who should buy what
  14   Hosted frontier models           the gap to the frontier: code, knowledge, cache, cost
  15   Power, heat and money            what a local run costs in watts and pence
  16   Uncensored and abliterated       what removing the refusal direction costs per axis
  17   DeepSeek's engine               why the hosted numbers look like that: model vs deployment
  18   For newcomers                    a build path, ten pitfalls, what this cost
  19   The same data, plotted           ten figures built from the archive
  20   Appendix                         commands, port map, file map, glossary
  21   Change log                       what each edition changed, and why
  22   Credits and tooling              who measured, what wrote the text
  23   Prior art                        the four other sources, and which question each answers

   Figures 1-24 · Tables 1-13
```
---

## 0. Executive summary

This document records a practical, repeatable method for deciding which local language models are
worth serving on a 128 GB unified-memory AMD Strix Halo machine, and it reports what that method
found across 33 models.

Seven claims are worth having up front, because everything else follows from them.

1. **Leaderboards do not answer the question.** A published benchmark score tells you how a model
   behaves on someone else's hardware, at someone else's prompt length, with someone else's sampler.
   On a bandwidth-limited integrated GPU, a model that is excellent in theory can be unusable in
   practice — too slow, too large, or quietly broken by a chat template. The only score that matters
   is the one this box produces at the caps this box will actually serve.

2. **The binding constraint is memory bandwidth, not capacity.** With 128 GB unified and a 100 GiB
   GPU-addressable pool, almost nothing this machine can run is too big. What separates models is
   how many bytes each generated token must read: a 26B model with 4B active parameters runs ~3x
   faster than a 31B dense model of similar size. Choosing a model here is mostly choosing an
   active-parameter count.

3. **A cheap gate catches most bad candidates.** Three probes — non-empty reply, valid JSON,
   one-word answer — cost under a second and rejected models that scored well on published code
   benchmarks. Run the gate first; do not spend an hour on HumanEval to discover the model repeats
   itself.

4. **Cap-burn is not the same as being wrong.** These models are scored at a fixed generation cap. A
   reasoning model that thinks past that cap returns nothing and is marked failed. Reading a score
   without reading the cap and the burn count is how good models get discarded and bad ones kept.

5. **Quantisation on this machine is a performance decision before it is a capacity decision.**
   Decode is bandwidth-bound, so fewer bits per weight means more tokens per second — measured at
   +22% and +43% in two pairs. The conventional "quantise only to fit" framing is a CUDA habit and
   gives the wrong answer here.

6. **Results do not transfer across a family in the way intuition suggests.** Code scores travel
   within ±2-3pp across a family at fixed quantisation; knowledge moved by 16.7pp and 50pp inside
   two families here, and speed does not transfer at all. §10 sets out exactly what may be inferred.

7. **The frontier's lead is axis-specific, and smaller than expected.** Measured with this harness,
   the best hosted model is 1.2pp ahead of the best local model on code — inside the noise — but
   5.8pp ahead on knowledge, and the cheap hosted tier scores *below* a local 30B on knowledge. §14
   has the numbers, the cache economics and the confounds.

The practical output of all this is a roster of 16 servable models with measured profiles, a
deployed daily driver — the uncensored QAT Q4_K_M build of gemma4-26b-a4b on port 8100, which since
2026-10-28 is what answers WhatsApp, with Ornith-1.5-35B-Uncensored on :8094 as the system boot model
— a documented set of models that were measured, failed or lost their slot and were deleted so nobody
repeats the work, and a measured comparison against hosted frontier models that establishes how large
the gap actually is. Port 8099 (the QAT Q4_0 driver named in earlier editions) still has its script
but its unit is disabled; only one model unit is enabled at a time and :8100 holds that slot.

---

## 1. Why test at all — the problem this solves

The obvious approach to picking a local model is to read a leaderboard, pick the top entry that fits
in memory, and run it. That approach fails on this class of hardware for four independent reasons.

**Reason 1: the hardware changes the ranking.** Benchmarks are usually run on data-centre GPUs with
tensor cores and hundreds of GB/s of HBM bandwidth. This machine has an integrated GPU with no
tensor cores and roughly a quarter of that bandwidth. Models are not uniformly penalised: a dense
30B model and a 26B mixture-of-experts model of the same file size can differ by 4x in tokens per
second. Published scores cannot tell you which side of that cliff a model sits on.

**Reason 2: quantisation changes capability, not just size.** A model at Q4 is not the model at
BF16. Most published scores are BF16. Here, some models hold up well at 4 bits and some collapse —
one 74B model scores 0.9451 on code at 2.06 bits per weight while another 74B model *of the same
architecture family* scores 0.1786. Same nominal recipe, wildly different outcome. Only measurement
distinguishes them.

**Reason 3: served configuration is part of the result.** A model's behaviour depends on its chat
template, whether reasoning is enabled, the KV-cache quantisation, the context length it was loaded
with, and the sampling parameters the server applies. One model here failed 20 of 20 code items
purely because its thinking mode was on and consumed the entire generation budget before emitting an
answer; with thinking off it scored 0.8659. Nothing about the weights changed. Any evaluation that
does not pin the serving configuration is not reproducible.

**Reason 4: the failure mode that matters is total, not incremental.** For an agent workload, a
model that emits invalid JSON once in twenty replies is not "95% good" — it breaks the loop. Three
probes catch this class of failure in under a second. That is why the harness has a gate before the
long tests rather than after.

The goal is therefore not "which model is best" in the abstract. It is: **for each axis of
capability this machine will be asked to perform, which model is the best available that is actually
servable here, and what does it cost in speed and memory to use it.**

---

## 2. The platform: what Strix Halo actually is

The box is a **Minisforum MS-S1 MAX** — `product_family: MINISFORUM`, `product_name: MS-S1 MAX`,
`sys_vendor: Micro Computer (HK) Tech Limited`, board `SHWSA` (Meigao ODM), BIOS 1.06, EC firmware
0.15. All of that is readable from DMI on the machine itself, which is the point of quoting it: it is
checkable rather than asserted. The hostname is deliberately not published — it is the operator's, not
the hardware's.

Two numbers describe this machine and explain most of its behaviour: about 100 GiB of
GPU-addressable memory, and roughly 256 GB/s of bandwidth shared between CPU and GPU.

### 2.1 Silicon and memory

Figure 1 — The memory topology: one pool, two address spaces.

```
   ┌─────────────────────────────────────────────────────────────────────┐
   │  AMD Ryzen AI MAX+ 395  ("Strix Halo")                              │
   │                                                                     │
   │   CPU: 16 Zen 5 cores / 32 threads        GPU: Radeon 8060S         │
   │        ~5.1 GHz boost                          RDNA 3.5, 40 CUs      │
   │                                                gfx1151               │
   │                                                no tensor cores       │
   │                                                                     │
   │   ┌───────────────────────────────────────────────────────────────┐ │
   │   │            ONE PHYSICAL MEMORY POOL — LPDDR5X                 │ │
   │   │            128 GB, 256-bit, ~256 GB/s nominal                 │ │
   │   │                                                               │ │
   │   │   ┌──────────────────┐        ┌────────────────────────────┐  │ │
   │   │   │  CPU addressable │◄──────►│  GPU addressable via GTT   │  │ │
   │   │   │  ~117 GiB usable │  same  │  up to 100 GiB (107.4 GB)  │  │ │
   │   │   └──────────────────┘  RAM   └────────────────────────────┘  │ │
   │   │                                        ▲                      │ │
   │   │                                        │ 8 GiB VRAM aperture  │ │
   │   │                                        │ (carve-out, unused)  │ │
   │   └───────────────────────────────────────────────────────────────┘ │
   └─────────────────────────────────────────────────────────────────────┘
```
Two numbers explain everything about this machine's behaviour:

- **GTT = 100 GiB.** This is the address space the GPU can map. It is not separate memory; it is the
  same LPDDR5X, mapped for the GPU. A 59 GB model fits. A 42.9 GiB model fits with room for KV
  cache. There is no 24 GB wall to design around, which is the single biggest difference from a
  consumer Nvidia card. - **~256 GB/s of bandwidth, shared between CPU and GPU.** Every generated
  token requires reading the active weights once. Bandwidth therefore sets the ceiling on tokens per
  second, and it is a *shared* resource: if the CPU is busy, decode slows.

### 2.2 Why this makes active parameters the key number

Figure 2 — Why active parameters, not parameter count, set decode speed.

```
   DENSE 31B at Q4 (~16.4 GiB)              MoE 26B with 4B active at Q4 (~13.4 GiB)
   ┌──────────────────────────────┐         ┌──────────────────────────────┐
   │ read ALL 16.4 GiB per token  │         │ read only the ~4B of experts │
   │                              │         │ that fire: ~2.5-3 GiB/token  │
   │      17 t/s  (measured)      │         │      49-60 t/s (measured)    │
   └──────────────────────────────┘         └──────────────────────────────┘
```
The dense model is smarter on knowledge (MMLU 0.8667 vs 0.8417) and 3x slower. That trade-off, not
raw parameter count, is the central decision on this box: **you are almost always choosing between
"reads 16 GB per token" and "reads 3 GB per token"**.

Measured effective bandwidth across the roster lands between roughly 120 and 280 GB/s depending on
quantisation, expert routing and context length. That spread is why the axis tables are empirical
and why a formula will only ever predict a new model to within ~40%. Use the tables; predict with
the formula only to rule a model out.

### 2.3 What is unusual, and what that costs

**Table 1 — What Strix Halo's properties cost.**

| Property | Consequence |
|---|---|
| 100 GiB GPU addressable | Models up to ~85 GiB are viable; 120B-class models at Q3/Q4 run |
| No tensor cores | Prompt processing (prefill) is 350-2900 t/s, far below an Nvidia card |
| Shared CPU/GPU bandwidth | Decode slows when the CPU is loaded; benches must run alone |
| iGPU only, RDNA 3.5 | ROCm support is partial; the mature path is Vulkan + llama.cpp |
| Laptop-class power | ~45-120 W package: quiet, cheap to run 24/7, no datacentre thermals |
| Unified memory | Loading a 60 GB model costs nothing but page cache; no model copying to VRAM |

The prefill number matters more than it looks. At 605 t/s prefill, a 30k-token agent prompt takes
~50 seconds before the first token appears. On this class of hardware, **long prompts are expensive
and long generations are cheap relative to a GPU** — the opposite of the instinct carried over from
Nvidia hardware.

---

## 3. The OS and driver stack

Every figure in this document was produced on one software stack, and the versions below are part of
the result: an older Mesa or kernel changes both correctness and speed on this GPU.

### 3.1 Verified versions

```
   Distro        CachyOS Linux (Arch-based, rolling)
   Kernel        7.3.0-5-cachyos
   CPU           AMD Ryzen AI MAX+ 395 w/ Radeon 8060S — 16C/32T
   GPU           Strix Halo [Radeon 8060S] (rev c1), gfx1151, RADV STRIX_HALO
   Mesa          26.2.5-arch3.1 at measurement time; 3:26.2.5-1 after the 2026-10-27 upgrade
   Vulkan        1.4.354 (RADV), OpenGL 4.6
   Memory        117 GiB visible, GTT total 100 GiB, VRAM aperture 8 GiB
   Runtime       llama.cpp 0.5.0-dev (build 3, commit 1a33095), ggml 0.25.3 — per-flavour
                 commits for every stage are in §4.1
```
CachyOS was chosen for three practical reasons: a rolling kernel new enough to have working
`amdgpu`/RADV support for gfx1151 without patching, x86-64-v3/v4 optimised package builds, and plain
Arch tooling when something needs to be rebuilt from source. Nothing in this document depends on
CachyOS specifically — Arch, Fedora and Ubuntu 25.x all work — but the Mesa version is the one
component you cannot be behind on. Older Mesa produces wrong output or outright failures on RDNA
3.5.

### 3.2 Why Vulkan rather than ROCm or CUDA

Figure 3 — The software stack: Vulkan and RADV, with no CUDA anywhere.

```
   ┌──────────────────────────────────────────────────────────────┐
   │  Application: llama-server                                   │
   ├──────────────────────────────────────────────────────────────┤
   │  ggml backend layer                                          │
   │     ggml-vulkan.so   ◄── used here: complete, stable, fast   │
   │     ggml-hip.so      ◄── partial gfx1151 support             │
   │     ggml-cpu.so      ◄── fallback, ~10x slower for decode    │
   ├──────────────────────────────────────────────────────────────┤
   │  Vulkan 1.4  →  RADV (Mesa)  →  amdgpu kernel driver         │
   │  no CUDA, no cuBLAS, no tensor cores, no vendor lock-in      │
   └──────────────────────────────────────────────────────────────┘
```
Every number in this document was produced on the Vulkan backend. That is a deliberate choice:

- **ROCm/HIP for gfx1151 is workable but not the mature path.** Support has improved through 2026,
  but the Vulkan backend needs no ROCm install, no version pinning, and no per-model kernel
  selection. - **CUDA does not exist here** and neither does the CUDA software ecosystem: vLLM,
  TensorRT-LLM, flash-attention kernels, bitsandbytes — all unavailable. This is the single largest
  practical difference from an Nvidia box, and it is why the harness talks to `llama-server`'s
  OpenAI-compatible endpoint rather than to a serving framework. - **Vulkan has one visible cost:**
  the first run of a new model or a new quantisation pays shader compilation. Benches warm up before
  measuring for exactly this reason; without the warmup, the first numbers are 2-5x too low.

---

## 4. The runtime: three llama.cpp trees and why

Three trees exist because architecture support is not uniform across llama.cpp builds, and what each
one is permitted to load is a deliberate boundary rather than an accident of history.

Figure 4 — The three llama.cpp trees and what each is permitted to do.

```
   ~/llama-local/
   ├── halo-box-strix-llama.cpp   ◄── SERVES EVERY UNIT
   │     Vulkan, GGML_NATIVE, custom kernels + MTP/dflash support.
   │     Build 0.5.0-dev, commit 1a33095. This is the production binary.
   │
   ├── prism-llama.cpp            ◄── exotic quant loader
   │     PrismML `prism` branch. Required for type-142 (PQ2_0) and
   │     blockwise-Hadamard weights that stock trees reject outright.
   │
   ├── upstream-llama.cpp         ◄── reference / new-arch bench tree
   ├── krafton-llama.cpp          ◄── LLM_ARCH_RAON1 only exists here
   └── sensenova-llama.cpp        ◄── has LLM_ARCH_SENSENOVA_U1, no converter
```
Three trees exist because **architecture support is not uniform**. `ggml-org/llama.cpp` is the
reference, but a model can be released against a vendor fork months before upstream support lands;
and a quantisation can require a loader patch that upstream does not carry. Keeping the trees
separate means a new architecture can be tested without endangering the binary that serves the
WhatsApp channel.

Build flags that matter on this box (from `build/CMakeCache.txt`):

```
-DCMAKE_BUILD_TYPE=Release
-DGGML_VULKAN=ON                     # the only GPU backend used
-DGGML_NATIVE=ON                     # tune for this Zen 5 / RDNA 3.5 part
-DGGML_CCACHE=OFF                    # ccache caused stale-kernel confusion
-DLLAMA_CURL=OFF                     # no runtime downloads in server
-DVulkan_INCLUDE_DIR=~/.local/include
-DVulkan_LIBRARY=/usr/lib/libvulkan.so
```
The last two are not optional: CMake's Vulkan discovery fails (FPHSA "Could NOT find Vulkan") on
this distro without them, which is the most common build failure reported for Strix Halo.

### 4.1 Build register — the commit behind each flavour, stage by stage

A path names a tree, not a build. `halo-box-strix-llama.cpp/build/bin/libggml-vulkan.so.0.25.3` is
character-identical before and after a `git pull`, so until 2026-10-27 the archive could not say
which code produced a number. Every measurement in §9 has therefore been re-attributed to a commit
from each tree's own history and its binary timestamps, and the harness now stamps the identity of
the serving build into every run.

```
   flavour (tree)              commit      server build string                ggml  measured
   ───────────────────────────────────────────────────────────────────────────────────────────
   halo-box-strix (fork)       4b2561e48   pre-identity: version not recorded  0.25.3  10-07 → 10-14
   halo-box-strix (fork)       065cd14f8   window: binary rebuilt 10-16 09:33  0.25.3  10-15 → 10-16
   halo-box-strix (fork)       1a3309516   0.5.0-dev (b3, commit 1a33095)      0.25.3  10-16 → 10-27
   upstream-llama.cpp          69f201a     0.6.0-dev (b1, commit 69f201a)      0.26.0  10-12
   upstream-master-bolt        a30fb49     0.7.0-dev (b1, commit a30fb49)      0.27.0  10-16 → 10-19
   kolibri-halo                bfce064     0.5.0-dev (b3, commit bfce064)      0.25.3  10-14
   flint-pr (retired)          unrecoverable — tree re-cloned 10-27            0.27.0  10-21 → 10-25
   flint-llama.cpp             19cce69     0.7.0-dev (b1, commit 19cce69)      0.27.0  10-27
   krafton-llama.cpp           fb89566     0.7.0-dev (b1, commit fb89566)      0.27.0  10-25
   prism-llama.cpp             b87ca72     0.2.0-dev (b1, commit b87ca72)      0.21.0  PQ2_0 only
   sensenova-llama.cpp         d854d98     0.7.0-dev (b1, commit d854d98)      0.27.0  never loaded
   hosted (api-shim)           n/a         route pinned per model (§14.1)       n/a     10-26
   ───────────────────────────────────────────────────────────────────────────────────────────
   b = the server's build number; ggml = the libggml-vulkan ABI version it links.
```
Four things the register settles, and one it refuses to:

- **The "0.5.0-dev" version belongs to the fork, not to the project.** Rows measured on the same day
  on `upstream-master-bolt` ran 0.7.0-dev, two minor versions ahead, because the trees are
  independent checkouts rather than branches of one repository. A score is not portable across
  flavours, and the ggml ABI moves with the flavour: 0.21 to 0.27 across this roster.
- **2026-10-16 is a discontinuity inside a single flavour.** 38 fork rows were measured on
  `4b2561e48` and 24 on `1a3309516` — the Bolt/Nemotron-VL cherry-pick and its follow-up revert.
  Rows either side of that rebuild are not the same binary, whatever the path says.
- **Most of the archive predates identity stamping**, so its commits are inferred rather than
  recorded: `exact` where one commit was HEAD across the whole window, `window` where a rebuild
  could have carried either. One row (gemma4-26b-a4b, 10-15 22:08) sits in that window and is a
  caveat on that measurement, not a fact about it.
- **flint's 10-21 → 10-25 rows cannot be attributed at all.** That tree was re-cloned on 10-27 and
  its earlier HEAD is gone, so those runs are labelled by tree and date only. This is precisely the
  cost of not recording the commit at the time.
- **What the register does not claim:** that a commit is a binary. A tree can be rebuilt from the
  same commit with different CMake flags, and only `build_dirty` plus the flags in §4 distinguish
  that case. Commit identity is necessary provenance, not sufficient.

From here on, every run's identity row carries `build_tree`, `build_abi`, `build_commit`,
`build_dirty`, `build_info` (the server's own string from `/props`, e.g. `b3-1a33095`) and
`build_version` (from `llama-server --version`), all written by `benchlib.build_identity()` before
the first test item runs. Legacy rows were annotated once with `~/bench/annotate-builds.py`.

---

## 5. Memory accounting and quantisation

Weights are only part of the footprint. KV cache scales linearly with context length and is charged
to the same 100 GiB pool:

```
   TOTAL GPU FOOTPRINT  =  weights  +  KV cache  +  compute buffers  +  mmproj (vision)

   weights        fixed by the quantisation        e.g.  13.4 GiB  (26B A4B at Q4_0)
   KV cache       ctx_tokens x layers x kv_heads x head_dim x 2 x bytes_per_elem
                  at q8_0 that halves; at f16 it doubles the q8_0 figure
   compute        ~1-2 GiB, grows with batch and ubatch
   mmproj         vision projector, 0.8-1.6 GiB when the model is multimodal

   WORKED EXAMPLE — a 4B model loaded at a genuine 1,048,576-token context:
     weights 3.3 GiB  +  KV 20.0 GiB  +  buffers ~1 GiB  =  ~24 GiB for a 4B model
     observed GTT: 35.5 -> 55.5 GiB once loaded
```
Two practical consequences:

1. **Context length is a memory purchase, and it is often the expensive part.** Serving a small
   model at a million tokens can cost more memory than serving a large model at 32k. The roster's
   default context is 32k-131k, not "maximum", for this reason. 2. **Quantise the KV cache.**
   `--cache-type-k q8_0 --cache-type-v q8_0` roughly halves KV footprint with no measurable quality
   cost on the axes tested here, and is applied to every unit.

How the pool is enforced — one resident model at a time, by mutual exclusion — is the subject of §6.
The remaining question about bytes is the encoding itself: how many bits each weight is stored in,
and what that costs in quality, capacity and speed. On this machine that is not a packaging detail
but a first-order performance decision, for the reason set out next.

---

### 5.1 What quantisation buys on this machine — speed, not just size

The standard framing is that quantisation trades quality for memory. On a discrete GPU that is
accurate: you quantise to make a model fit, and the card's bandwidth was never the limit. On Strix
Halo the trade is different, and it is worth stating plainly because it changes how the choice
should be made.

Decode is bandwidth-bound: each generated token requires reading the active weights once. Fewer
bytes per weight therefore means more tokens per second, near-linearly, until some other limit
bites. **On this box, quantising is a performance decision first and a capacity decision second.**

Figure 5 — Bytes read per token determine decode speed.

```
   same 12.1B model, two quantisations            same 30.1B model, two quantisations

   Q6_K   10.1 GiB  ──►  91.8 t/s                Q8_0   34.6 GiB  ──►  52.3 t/s
   Q4_K_M  7.5 GiB  ──► 111.9 t/s (+22%)         Q4_K_M 17.0 GiB  ──►  74.7 t/s (+43%)
            ▲                                              ▲
            └── also 2.6 GiB smaller                       └── also half the memory
```
The consequence is a genuinely different optimum from the CUDA world. There, Q4 is the common
default because it fits; here it is the default because it is *faster as well as smaller*, and the
only reason to climb the ladder is a measurable quality gain that you can justify on an axis you
care about. The next subsection quantifies what those gains actually are on this hardware.

### 5.2 The ladder, with the rungs this box has actually visited

**Table 2 — Practical quantisation ladder (bpw approximate; sizes = file size on disk).**

```
   quant      bpw   12B      26B      120B     status on this box
   ─────────────────────────────────────────────────────────────────────────────────────
   Q8_0       8.5   12.8G    27.9G    129G     measured: +2.5pp MMLU, −30% decode
   Q6_K       6.6   10.1G    21.6G    100G     measured: best quality/speed balance for small models
   Q5_K_M     5.7    8.7G    18.6G     86G     used where 26B+ quality matters and Q4 shows loss
   Q4_K_M     4.9    7.5G    16.0G     74G     measured: the practical default for 20B+
   Q4_0       4.5    6.9G    14.7G     68G     measured: QAT driver lives here (13.4 GiB file)
   Q3_K_M     3.9    6.0G    12.8G     59G     measured: usable; knowledge starts to slip
   IQ3_S      3.4    5.2G    11.2G     52G     measured: knowledge collapse in one case (0.0083)
   IQ3_XXS    3.1    4.7G    10.2G     47G     measured: 0.5610 HE from a 35B — avoid untested
   IQ2_XXS    2.1    3.2G     6.9G     32G     measured: code survives, knowledge collapses (0.3667)
   IQ1_M      1.8    2.7G     5.9G     27G     not tested here; expect further knowledge loss
   ─────────────────────────────────────────────────────────────────────────────────────
   rule: ≥Q4_K_M for anything that must know facts; Q2/IQ2 only for procedural work that
         has been measured at that quant; below 2 bpw, expect breakage rather than degradation.
```
Sizes above are `params × bpw ÷ 8` plus ~3% overhead, and match the files on disk to within a
percent. They are worth internalising because they predict two things at once: whether the model
fits, and roughly how fast it will decode relative to a sibling.

### 5.3 Four measured pairs that isolate the variable

Opinions about quantisation are cheap; this box produced four pairs where only one thing changed.

**Table 3 — Same model or same base, one variable altered.**

```
   change                                   HE        MMLU      decode     note
   ───────────────────────────────────────────────────────────────────────────────────────
   hy-memory Q4_K_M → Q8_0                  0.7805    0.7250    74.7 t/s   baseline
                                            0.7683    0.7500    52.3 t/s   −1.2pp code, +2.5pp
                                                                          knowledge, −30% speed
   gpt-oss base → abliterated (same quant)  0.9268    0.5833    50.1 t/s   baseline
                                            0.9268    0.7500    50.5 t/s   code identical,
                                                                          knowledge +16.7pp
   mellum Q6_K official → Q4_K_M fork       0.8780    0.7000    91.8 t/s   baseline
                                            0.9146    0.8083   111.9 t/s   SMALLER quant scored
                                                                          better on both axes
   gemma4-26b Q8_0 → QAT Q4_0               0.9573    0.8667    49.4 t/s   25.0 GiB file
                                            0.9512    0.8417    59.5 t/s   13.4 GiB file
                                            −0.6pp code, −2.5pp knowledge, +21% decode,
                                            11.6 GiB smaller — the QAT file is the one to ship
   ───────────────────────────────────────────────────────────────────────────────────────
```
Three conclusions that are not the conventional ones:

1. **Quantisation does not uniformly cost quality.** In two of four pairs the smaller or more
   aggressively quantised variant scored *better* on at least one axis — the importance-matrix Q4_K_M
   beats the vendor Q6_K by 3.7pp code and 10.8pp knowledge, and the 8-bit→4-bit QAT step in the gemma
   pair costs only 0.6pp of code. Quantisation error is not monotonic in bits per weight when the
   recipe changes as well. 2. **Knowledge is the axis that moves; code barely does.** Across the four
   pairs code moved by at most 3.7pp and usually by under 1.2pp, while knowledge moved from −2.5pp to
   +16.7pp. If you must quantise aggressively and you care about facts, you are spending the wrong
   currency. 3. **A good 4-bit is the right default, and QAT is worth preferring when it exists.** The
   gemma QAT file gives up 0.6pp of code and 2.5pp of knowledge for 21% more decode and 11.6 GiB less
   resident memory — the difference between a 25 GiB and a 13.4 GiB footprint, which on a box that also
   runs CCTV recording and a hardware monitor is not a rounding error. What the channel actually runs
   is the *uncensored* Q4_K_M (0.9573 / 0.8500 at 56.9 t/s), chosen for refusal behaviour first: at the
   4-bit rung the three gemma encodings are 0.6-0.8pp apart on code and 0.8-2.5pp on knowledge, so
   behaviour, speed and footprint — not the last code point — decide it.

### 5.4 Naming: K-quants, I-quants, UD and QAT are not interchangeable

Four labels get treated as synonyms and are not. The distinction matters because it explains why a
"Q4" is sometimes better than a "Q6".

```
   K-quant   Q4_K_M, Q5_K_M, Q6_K     block-wise, the mature default; M = medium mix
   I-quant   IQ2_XXS, IQ3_S, IQ4_XS   importance-matrix driven; smaller at equal quality,
                                      but more sensitive to a bad imatrix — and the source
                                      of every catastrophic row in this document
   UD        UD-Q4_K_XL, UD-Q6_K_XL   "unsloth dynamic": per-tensor quantisation, sensitive
                                      tensors kept at higher precision. Not comparable to
                                      plain Q4_K_M at the same nominal label.
   QAT       gemma-4-26B_q4_0-it      quantisation-aware training: the model was trained to
                                      tolerate the quantisation it ships with
```
Practical consequence: **never compare across naming schemes by the number alone.** `UD-Q4_K_XL` is
larger and better than `Q4_K_M`; `IQ4_XS` is smaller than `Q4_K_M` and roughly comparable in quality
when the imatrix is good and much worse when it is not. The only reliable comparison is the one made
on this hardware, which is why the roster records the exact file name and bpw next to every score.

### 5.5 KV-cache quantisation is a separate decision

Weight quantisation and KV-cache quantisation are independent, and conflating them leads to wrong
predictions about context cost. Measured on this box by loading the driver at two context lengths
and differencing the GTT footprint:

```
   gemma4-26b-qat-q4, q8_0 KV, single slot
     @ 16,384 tokens   GTT +14.46 GiB
     @131,072 tokens   GTT +15.84 GiB
     ──────────────────────────────────────
     Δ 1.38 GiB over 114,688 tokens  →  12.6 KB per token
     implied KV:  0.39 GiB @32k  ·  1.58 GiB @131k  ·  ~3.2 GiB @131k if KV were f16
```
Two observations worth carrying away:

- **Context is cheap for this architecture and expensive for others.** 12.6 KB/token is small
  because most of the model's attention layers are sliding-window, so only a minority of layers grow
  with context. Contrast the 4B Spark-X2.6 measured the same way: ~20 KB/token, 20 GiB for a
  1M-token window — six times more KV per token from a model a sixth the size. - **The saving from
  q8_0 KV is real but bounded.** Halving KV precision halves the KV term; if the KV term is 1.6 GiB
  at 131k, the saving is 1.6 GiB, not 13 GiB. Decide based on measurement for the specific
  architecture, not on a rule of thumb.

Every unit on this box runs `--cache-type-k q8_0 --cache-type-v q8_0`. On the axes measured here it
cost nothing detectable, and it is the reason 131k contexts fit alongside a 74 GiB model in the same
session budget.

### 5.6 How quantisation fails, and how to choose

Four failure modes were observed, all of them avoidable with one minute of inspection:

```
   1. LOADER REJECTION          tensor 'output.weight' has invalid ggml type 142
                                → the quant uses PQ2_0 + blockwise-Hadamard; stock trees
                                  refuse it. Requires the prism tree (see §4).

   2. SILENT QUALITY COLLAPSE   qwen38fn-abl IQ3_S: HE 0.8476, MMLU 0.0083
                                177B of model that can write code and cannot answer
                                a multiple-choice question. Caught only by running
                                MMLU — nothing about the load looks wrong.

   3. AXIS-SPECIFIC COLLAPSE    Nemotron-Bolt IQ2_XXS: HE 0.9451, MMLU 0.3667
                                procedural skill survives, factual recall does not.

   4. TOTAL BREAKAGE            same nominal recipe, different file: HE 0.1786.
                                Two IQ2_XXS loads of one architecture family, one
                                excellent, one unusable.
```
Choosing a quantisation, in order:

Figure 6 — Choosing a quantisation.

```
   ┌─────────────────────────────────────────────────────────────────────────────┐
   │ Does the model fit at Q4_K_M with room for KV at the context you need?      │
   │    yes ──► use Q4_K_M (or a QAT file if one exists — prefer it)             │
   │    no  ──► do you need factual knowledge from it?                           │
   │             no  ──► IQ3_XXS / IQ4_XS is acceptable; measure riddles + preflight
   │             yes ──► shrink context, shrink the model, or use a smaller      │
   │                     quant AND run MMLU before trusting it                   │
   └─────────────────────────────────────────────────────────────────────────────┘
   Never: pick a quant below Q4 because the file is smaller, without measuring the
   axis you intend to use. One MMLU run costs 20 minutes and catches the 0.0083 case.
```
## 6. The serving architecture

One model is resident at a time, enforced by systemd rather than by convention — and that
exclusivity is both what makes the memory budget safe and what creates an availability risk the
guard has to manage.

### 6.1 One model at a time, fourteen ways

Figure 7 — Fourteen mutually exclusive user units plus one system unit, one resident model.

```
                      ┌───────────────────────────┐
                      │  llama-switch <model>     │   user-facing verb
                      └─────────────┬─────────────┘
                                    │  stop every other unit (via Conflicts=)
                                    ▼
        ┌───────────────────────────────────────────────────────────┐
        │  14 x systemd --user units:  llama-<model>.service         │
        │  each Conflicts= every other one  =>  exactly one loads    │
        │                                                            │
        │  8082 qwen3next      8083 qwen3next-q6    8084 ornith-122b │
        │  8085 gptoss         8086 ornith           8093 qwen38-35b │
        │  8096 gptoss-abl     8097 qwen38fn-abl     8099 gemma-qat   │
        │  8100 gemma-uncen    8181 lfm25            8185 ornith-mtp  │
        │  8186 minicpm-v47    8189 nemotron-super   8098 ornith35b   │
        │                                                            │
        │  + orient-ornith.service (SYSTEM unit, :8094, boot model)   │
        └───────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                      ┌───────────────────────────┐
                      │  127.0.0.1:<port>/v1      │  OpenAI-compatible
                      └───────────────────────────┘
```
Why this shape rather than one server with dynamic loading: `Conflicts=` gives an atomic guarantee
that exactly one model owns the GPU, which is what this machine's memory budget requires, and it
survives crashes. Why it is dangerous: **every switch kills the model serving WhatsApp.** That risk
is what the guard exists to manage.

### 6.2 The availability guard

Because the daily driver also serves the WhatsApp channel, an accidental swap is a silent outage —
the phone shows no error, messages simply stop being answered.

Figure 8 — The availability guard: intent, deliberate-switch test, restart budget.

```
   every 60s (timer)                       llama-model-guard.sh
   ┌──────────────────────────────────────────────────────────────────┐
   │ 1. read ~/llama-local/.intent-model   (written by llama-switch    │
   │    on every successful start)                                    │
   │ 2. is the intended model's port listening?                        │
   │      yes -> exit                                                  │
   │      no  -> was the resident model started LATER than the intent? │
   │              yes -> deliberate switch; leave it alone             │
   │              no  -> restart the intended model                    │
   │ 3. budget: max 3 gateway restarts/hour (./.guard-restarts)        │
   │ 4. escape hatch: GUARD_SKIP_BRIDGE=1 for maintenance              │
   └──────────────────────────────────────────────────────────────────┘
```
The rule that makes this safe is step 2's "deliberate switch" test: if you intentionally started
another model, the guard must not fight you by dragging the driver back. Only an *unexplained*
absence of the intended model triggers a restart.

### 6.3 Bench isolation

Benchmarks run through transient units (`systemd-run --user --collect --unit=bench-<name>`), which
do **not** participate in `Conflicts=`. That is how a two-hour HumanEval run on a 79 GB model left
the WhatsApp channel answering throughout. Any benchmark that used `llama-switch` would drop the
driver and take the channel down with it.

---

## 7. The harness

Seven axes, each answering exactly one question, scored by exact match or executed code rather than
by another model — and one knob, the generation cap, that moves scores further than most model
changes do.

### 7.1 Design principles

`~/bench` is a small, self-contained harness with six rules that turned out to matter more than any
individual test:

1. **No external judge, no API calls.** Every axis is scored by exact match, executable test, or
   JSON parse. Nothing depends on a model grading a model, so results are reproducible offline and a
   network outage cannot silently change a score. 2. **Caps are recorded per row.** The generation
   cap, the item count, and the quantisation go into `~/runs/catalogue.json` next to the score. A
   number without its cap is not a result. 3. **The gate runs before the expensive axes.** Preflight
   is cheap and diagnostic; running it last wastes the hour that HumanEval costs. 4. **Report empty
   answers separately from wrong answers.** These are different failures — one is a budget artefact,
   the other is a capability limit — and conflating them is how models get misjudged. 5. **Every
   axis writes to JSONL as it completes.** A crashed or aborted run still yields partial evidence,
   which is the difference between "unknown" and "abandoned for a documented reason". 6. **Record
   the build, not just the tree.** The identity row carries the serving commit, the ggml ABI, the
   server's own build string and a dirty flag (§4.1). Without them, a re-measure after a `git pull`
   looks identical to the original run — which is the gap that had to be reconstructed by hand for
   everything measured before 2026-10-27.

### 7.2 The seven axes

```
   ┌──────────────┬──────────────────────────────────────┬──────────┬────────────────────┐
   │ AXIS         │ WHAT IT MEASURES                     │ COST     │ SCORED BY          │
   ├──────────────┼──────────────────────────────────────┼──────────┼────────────────────┤
   │ perf         │ prefill, decode, time-to-first-token │ seconds  │ llama timings      │
   │ preflight    │ gate: does it reply, JSON, one word   │ <1 s     │ exact / JSON parse │
   │ needle 2k/8k │ retrieval from mid-context           │ seconds  │ exact substring    │
   │ riddles      │ 14 reasoning + arithmetic traps      │ minutes  │ exact match        │
   │ HumanEval    │ 164 coding problems, unit-tested     │ 20 min-2h│ pytest execution  │
   │ MMLU-Pro     │ 120 knowledge MCQs                   │ 20-50 min│ exact letter       │
   │ IFEval       │ 30 instruction-following constraints │ 10 min   │ lm-eval strict acc │
   └──────────────┴──────────────────────────────────────┴──────────┴────────────────────┘
```
**perf** — warms up, then sends a ~2000-token prompt and asks for a fixed 128-token reply with
prompt caching disabled. Reports prefill tokens/s (`pp`), decode tokens/s (`tg`) and time-to-first-
token. The warmup exists because Vulkan shader compilation and cold page cache distort the first
measurement by 2-5x.

**preflight** — three probes, each chosen because it catches a specific real failure:

```
   content_nonempty      "Reply with exactly: OK"
       catches: broken chat template, immediate EOS, empty output

   json_schema           'Return a JSON object with exactly one key "status" and value "ok"'
       catches: tool-calling breakage. An agent that cannot emit clean JSON
                cannot call a tool. Observed failure: repeating the same object
                four times back to back.

   instruction_one_word  "What is the capital of France? Answer with exactly one word."
       catches: models that argue with the format. Observed failure: "Paris. Wait,
                let me reconsider—the period might count as punctuation…"
```
A model that fails any of these is not served, regardless of its code score. One measured model
(REAP50-pruned Ornith) scored well on its publisher's HumanEval harness and failed 2 of these 3.

**needle 2k / 8k** — a unique token is planted in the middle of filler text and must be quoted back.
Deliberately generous on budget (256 tokens, retried at 4x if the model ran out while thinking) so
that "cannot retrieve" is not confused with "ran out of room to think". This is a floor test:
failing it disqualifies a long-context model, passing it does not prove long-context quality.

**riddles + arithmetic (14 probes)** — five classic riddles and arithmetic traps. The traps are the
valuable part: `9.11 vs 9.9` catches lexicographic float comparison, and the bat-and-ball problem
catches the intuitive-but-wrong 10-cent answer. Tested with exact-match on a substring list, so a
correct answer inside a verbose explanation still passes.

**HumanEval (164 problems)** — the code axis, and the only axis where scoring is objective by
construction: candidate function bodies are executed against unit tests. A model cannot bluff a
passing implementation. This is the most expensive axis (20 minutes to 2 hours) and the one most
worth running only after preflight.

**MMLU-Pro (120 questions)** — four-option knowledge questions, scored on the exact option letter.
Separates "knows things" from "can code", which are frequently different models here: the fastest
model on the box (mellum21, 111.9 t/s) is mid-pack on knowledge, and the best knowledge model on
record (gemma4-31b, retired 2026-10-30) was the second slowest; the best one still on disk
(gemma4-26b-uncen, 0.8500) runs at 56.9 t/s.

**IFEval (30 prompts)** — instruction-following constraints (lowercase only, exactly N paragraphs,
JSON with specific keys). Run through `lm-eval`'s `local-chat-completions` task. This axis carries
the harness's biggest known trap, described next.

### 7.3 The cap — the knob that changes scores more than the model does

Figure 9 — The cap spectrum, and the same weights at two budgets.

```
   CAP = maximum tokens a model may generate for ONE test item.

   cap 512   ├────────┤                 floor estimate; thinking models truncate always
   cap 2048  ├──────────────────┤       harness default; fine for non-reasoning models
   cap 4096  ├────────────────────────┤ room to think; used for most large models
   cap 8192  ├────────────────────────────────────────┤ only for models that need it

   SAME MODEL, SAME WEIGHTS, TWO BUDGETS:
     sage-a1.5, thinking ON  @4096    ->  0/20 HumanEval passes (every item hit the cap)
     sage-a1.5, thinking OFF          ->  0.8659 (142/164)
   SAME TASK, TWO BUDGETS:
     lfm25 IFEval via lm-eval (pinned 1280)  ->  0.3333
     lfm25 IFEval standalone @4096           ->  0.9333
```
Two rules follow, and they are the ones most often violated when reading these tables:

- **Compare within a cap band.** A row at cap 512 is a lower bound, not a measurement. `qwen38-35b`
  at 0.8537 (cap 512) is not necessarily a worse coder than `mellum` at 0.8780 (cap 4096). - **Count
  the burns.** If 17 of 60 items returned empty after exhausting the budget, the mean understates
  the model. Cite the burn count next to the score or the number lies by omission.

`lm-eval`'s IFEval task pins `max_gen_toks` internally and ignores the model argument, which is why
the archive shows one nonsensical IFEval row. It is recorded as an artefact, not a result.

### 7.4 Budgetting and artefacts

A full sweep is expensive, so `t20` accepts a wall-clock budget and allocates it across axes
proportionally to each axis's cost at the model's measured speed:

```
   t20 --port 8099 --core                      # quick pass: perf, preflight, needles, riddles
   t20 --port 8099 --max-gen-toks 4096         # + HumanEval 164, MMLU-Pro 120, IFEval 30
   t20 --port 8099 --budget 1800 --tag mysweep # cap total wall time
```
Artefacts: `~/runs/<timestamp>-<tag>.jsonl` (per-item rows) and `~/runs/catalogue.json` (one row per
axis per model, the file every table in this document is derived from).

---

## 8. How to read the results that follow

Five rules, in order of how much damage ignoring them causes:

1. **A score without a cap is meaningless.** Every row below states its cap where it differs from
   the axis default (HumanEval/MMLU 2048, riddles 4096). 2. **n matters.** `qwen35` at 0.9242 is a
   66-item measurement; `gemma4-31b` at 0.9634 is 164 items. The first has roughly ±3 pp of standard
   error, the second ±1.3 pp. Do not rank across different n without noting it. 3. **Preflight 0/3
   does not mean the model is bad at its job.** `minicpm-v47-35b` fails all three preflight probes
   and is still the box's best vision model. It refuses bare chat-format probes because its template
   expects image content. Preflight is a gate for *chat and agent* use, not a universal quality
   measure. 4. **Empty ≠ wrong.** Riddle failures marked empty are usually budget exhaustion, not
   misunderstanding. Check the content, not just the verdict. 5. **Speed is measured alone.** These
   numbers were taken with nothing else on the GPU. Concurrent benchmarks halve decode throughput —
   one model measured 19.5 t/s under contention and 46.9 t/s alone.

**Conventions used throughout.** Speeds appear as `t/s` inside tables and diagrams and as "tokens
per second" in prose; they are the same unit. `pp` is prefill (prompt processing) and `tg` is decode
(token generation). Scores are proportions in 0-1, not percentages. `HE` abbreviates HumanEval, and
`MMLU` in compact score notation means MMLU-Pro; the full suite name is written out wherever the
distinction matters. A "cap-burn" is an item that produced no answer because it exhausted its
generation budget. Section numbers written as §n refer to this document.

Two forward pointers: **§10** states what may and may not be inferred from one model to another in
the same family, and **§5.1-5.6** cover quantisation, which is the variable most often confused with
model quality in comparisons of this kind.

---

## 9. Results — the measured matrix

One row per model ever measured, best-measured run. `HE` is `score (items@cap)`; caps differ, so read
section 7.3 before ranking. Prefill/decode are single-tenant measurements. Every row also has a build
identity — the flavour and commit that produced it — tabulated in §4.1, and recorded per run from
2026-10-27 onwards. The `build` column names the tree and the commit that produced the row — `fork b3-1a33095`, `bolt
b1-a30fb49`, or `pre-identity` where the run predates identity stamping (§4.1 explains why that is a
window, not a guess). The full path is deliberately not published. The `measured` column is the date of the best-scoring run shown — the run id and the full build
identity are in `data/catalogue.json`, so any row can be traced to the exact binary that produced it.
The `disk` column is the roster as of **2026-10-30**: `✓` present and servable,
`✗` retired (recipes in `~/llama-local/RETIRED-models.md`). Table 4 is all-time by design — the
deleted rows are why the recommendations below have reasons.

**Table 4 — The measured matrix, all-time: one row per model, best run, caps shown with item counts.**

| Model | Params | Quant | HumanEval | MMLU-Pro | Riddles | prefill t/s | decode t/s | measured | build | disk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma4-31b | 30.7B | Q4_0 | 0.9634 (164@2048) | 0.8667 (120@2048) | 14/14 | 350 | 17.0 | 2026-10-21 | fork pre-identity | ✗ 10-30 |
| gemma4-26b-uncen | 25.2B | Q4_K_M | 0.9573 (164@2048) | 0.8500 (120@2048) | 14/14 | 1759 | 56.9 | 2026-10-28 | fork b3-1a33095 | ✓ driver |
| minicpm-v47-35b | 34.7B | Q6_K | 0.9573 (164@4096) | 0.7750 (120@4096) | 10/14 | 1600 | 64.6 | 2026-10-18 | bolt pre-identity | ✓ |
| gemma4-26b-a4b | 25.2B | Q8_0 | 0.9573 (164@2048) | 0.8667 (120@2048) | 14/14 | — | 49.4 | 2026-10-30 | fork b3-1a33095 | ✗ 10-30 |
| gemma4-26b-qat-q4 | 25.2B | Q4_0 | 0.9512 (164@2048) | 0.8417 (120@2048) | 14/14 | 1900 | 59.5 | 2026-10-21 | fork pre-identity | ✓ |
| ornith-122b | 124.6B | Q4_K_M | 0.9512 (164@4096) | 0.7917 (120@4096) | 12/14 | 605 | 23.3 | 2026-10-20 | fork pre-identity | ✓ |
| nemotron-super-120b | 123.6B | Q3_K_M | 0.9512 (164@4096) | 0.7667 (120@4096) | 11/14 | 411 | 27.1 | 2026-10-18 | bolt pre-identity | ✓ |
| Nemotron-Bolt-74B-A9B | 74.0B | IQ2_XXS | 0.9451 (164@2048) | 0.3667 (120@2048) | 13/14 | 577 | 72.8 | 2026-10-16 | bolt pre-identity | ✗ 10-30 |
| qwen3next-q6 | 79.7B | Q6_K | 0.9296 (142) | 0.6058 (104) | 14/14 | 1189 | 45.8 | 2026-10-10 | fork pre-identity | ✓ |
| gptoss | 116.8B | MXFP4 | 0.9268 (164) | 0.5833 (120) | 12/14 | 1045 | 50.1 | 2026-10-12 | fork pre-identity | ✓ |
| gptoss-abliterated | 116.8B | MXFP4 | 0.9268 (164@2048) | 0.7500 (120@2048) | 10/14 | 1052 | 50.5 | 2026-10-13 | fork pre-identity | ✓ |
| qwen35 | 122.1B | Q4_K_M | 0.9242 (66) | 0.5417 (48) | 12/14 | 622 | 22.9 | 2026-10-11 | fork pre-identity | ✗ |
| ornith-mtp-21g | 35.5B | IQ4_XS | 0.9207 (164@4096) | 0.7750 (120@2048) | 11/14 | 1610 | 65.2 | 2026-10-17 | fork pre-identity | ✓ |
| flint (i1-Q4_K_M) | 40.0B | Q4_K_M | 0.9167 (60@4096) | — | 10/14 | — | 71.1 | 2026-10-25 | flint pre-identity | ✗ 10-30 |
| qwen3next-q4 | 79.7B | Q4_K_M | 0.9146 (164@2048) | 0.7417 (120@2048) | 14/14 | 1219 | 58.1 | 2026-10-31 | fork b3-1a33095 | ✓ |
| mellum21-fork | 12.1B | Q4_K_M | 0.9146 (164@8192) | 0.8083 (120@8192) | 10/14 | 2723 | 111.9 | 2026-10-18 | fork pre-identity | ✓ |
| mellum | 12.1B | Q6_K | 0.8780 (164@4096) | 0.7000 (120@4096) | 11/14 | 2442 | 91.8 | 2026-10-12 | fork pre-identity | ✗ 10-29 |
| qwen38-35b | 35.5B | Q4_K_M | 0.8537 (164@512) | 0.5083 (120@512) | 13/14 | 1560 | 68.3 | 2026-10-12 | fork pre-identity | ✓ |
| lfm25-24b-a2b | 24.0B | Q4_0 | 0.8537 (164@4096) | 0.6917 (120@4096) | 10/14 | 2930 | 106.6 | 2026-10-17 | fork pre-identity | ✓ |
| qwen38fn-abl | 176.9B | IQ3_S | 0.8476 (164@2048) | invalid (1/120) | 11/14 | 448 | 52.9 | 2026-10-13 | fork pre-identity | ✓ |
| qwen36-35b | 34.7B | Q4_K_M | 0.8354 (164) | 0.4500 (120) | 12/14 | 1548 | 57.1 | 2026-10-12 | fork pre-identity | ✗ |
| Ornith-1.5-35B | 35.5B | Q4_K_M | 0.8232 (164@512) | 0.4167 (120@512) | 13/14 | 1629 | 72.5 | 2026-10-12 | fork pre-identity | ✓ |
| kimi | 49.1B | Q4_K_M | 0.7866 (164@2048) | 0.5500 (120@2048) | 13/14 | 1597 | 67.4 | 2026-10-14 | fork pre-identity | ✗ 10-29 |
| hy-memory-30b-a3b | 30.1B | Q4_K_M | 0.7805 (164@2048) | 0.7250 (120@2048) | 12/14 | 1515 | 74.7 | 2026-10-17 | fork pre-identity | ✗ 10-29 |
| graft-50b-a3b | 50.7B | Q4_K_M | 0.7805 (164@2048) | 0.6583 (120@2048) | 14/14 | 1368 | 54.3 | 2026-10-19 | fork pre-identity | ✗ |
| hy-memory-30b-a3b-q8 | 30.1B | Q8_0 | 0.7683 (164@2048) | 0.7500 (120@2048) | 11/14 | 1459 | 52.3 | 2026-10-17 | fork pre-identity | ✗ 10-29 |
| Ling-3.0-flash | — | Q4_K_M | — | 0.7667 (120@2048) | 11/14 | — | 43.5 | 2026-10-22 | fork pre-identity | ✗ 10-30 |
| ornith35b (uncensored) | 35.5B | IQ3_XXS | 0.5671 (164@4096) | 0.6333 (120@4096) | 12/14 | 1762 | 69.9 | 2026-10-31 | fork b3-1a33095 | ✓ boot |
| nemotron-bolt (broken load) | 74.0B | IQ2_XXS | 0.1786 (56@512) | 0.4146 (41@512) | 8/14 | 586 | 22.7 | 2026-10-21 | fork pre-identity | ✗ 10-30 |
New in this edition: the `gemma4-26b-uncen` row (measured 2026-10-28, the model that now answers the
channel) and the `disk` column. **Three rows were wrong in version 1.2 and are corrected.** `qwen3next-q6`
was published as 0.9207 (164@2048) — no run supports that: its best is 0.9296 over 142 items, and
0.9207 is `ornith-mtp-21g`'s figure, copied onto it. `nemotron-super-120b` reads 0.9512 (156/164) at
cap 4096 rather than 0.9329; two runs exist (156/164 and 153/164) and the old row quoted neither
cleanly. And `gemma4-26b-a4b` and `gemma4-26b-qat-q4` were listed as two models when they are **one
weight file measured twice** (156/164 and 154/164, cap 2048, MMLU 101/120 in both): the run alias was
shared across the Q8_0 and QAT files, which is how a table comes to compare a file with itself. The
Q8_0 row now carries its own file's numbers.


**Table 4b — what is actually servable on 2026-10-31.** Sixteen artefacts, every one now carrying a
capability row. Full inventory (15 model units, 602 GiB, projectors and drafters included) is in §20.3.

| Model | Quant | HumanEval | MMLU-Pro | Riddles | decode t/s | measured | build | endpoint |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma4-26b-uncen | Q4_K_M | 0.9573 (164@2048) | 0.8500 (120@2048) | 14/14 | 56.9 | 2026-10-28 | fork b3-1a33095 | :8100 enabled |
| minicpm-v47-35b | Q6_K | 0.9573 (164@4096) | 0.7750 (120@4096) | 10/14 | 64.6 | 2026-10-18 | bolt pre-identity | :8186 |
| gemma4-26b-qat-q4 | Q4_0 | 0.9512 (164@2048) | 0.8417 (120@2048) | 14/14 | 59.5 | 2026-10-21 | fork pre-identity | :8099 script only |
| ornith-122b | Q4_K_M | 0.9512 (164@4096) | 0.7917 (120@4096) | 12/14 | 23.3 | 2026-10-20 | fork pre-identity | :8084 |
| nemotron-super-120b | Q3_K_M | 0.9512 (164@4096) | 0.7667 (120@4096) | 11/14 | 27.1 | 2026-10-18 | bolt pre-identity | :8189 |
| qwen3next-q6 | Q6_K | 0.9296 (142) | 0.6058 (104) | 14/14 | 45.8 | 2026-10-10 | fork pre-identity | :8083 |
| gptoss | MXFP4 | 0.9268 (164) | 0.5833 (120) | 12/14 | 50.1 | 2026-10-12 | fork pre-identity | :8085 |
| gptoss-abliterated | MXFP4 | 0.9268 (164@2048) | 0.7500 (120@2048) | 10/14 | 50.5 | 2026-10-13 | fork pre-identity | :8096 |
| ornith-mtp-21g | IQ4_XS | 0.9207 (164@4096) | 0.7750 (120@2048) | 11/14 | 65.2 | 2026-10-17 | fork pre-identity | :8185 |
| mellum21-fork | Q4_K_M | 0.9146 (164@8192) | 0.8083 (120@8192) | 10/14 | 111.9 | 2026-10-18 | fork pre-identity | — |
| qwen3next-q4 | Q4_K_M | 0.9146 (164@2048) | 0.7417 (120@2048) | 14/14 | 58.1 | 2026-10-31 | fork b3-1a33095 | :8082 |
| qwen38-35b | Q4_K_M | 0.8537 (164@512) | 0.5083 (120@512) | 13/14 | 68.3 | 2026-10-12 | fork pre-identity | :8093 |
| lfm25-24b-a2b | Q4_0 | 0.8537 (164@4096) | 0.6917 (120@4096) | 10/14 | 106.6 | 2026-10-17 | fork pre-identity | :8181 |
| qwen38fn-abl | IQ3_S | 0.8476 (164@2048) | invalid (1/120) | 11/14 | 52.9 | 2026-10-13 | fork pre-identity | :8097 |
| Ornith-1.5-35B | Q4_K_M | 0.8232 (164@512) | 0.4167 (120@512) | 13/14 | 72.5 | 2026-10-12 | fork pre-identity | :8086 |
| ornith35b (uncensored) | IQ3_XXS | 0.5671 (164@4096) | 0.6333 (120@4096) | 12/14 | 69.9 | 2026-10-31 | fork b3-1a33095 | :8094 boot |
The last blank cell was filled on 2026-10-31: `Qwen3-Next-80B UD-Q4_K_XL` now has a full row
(0.9146 code, 0.7417 knowledge, 14/14, 58.1 t/s) and it is the weakest large model on disk — see §9.1
and §21. Every artefact in this table has been scored on both capability axes.



Models measured on the core axes only (no HumanEval row, all-time): `qwen38-flash-next-abl`
(31.5 t/s, retired 10-30), `coder390-abl` (16.3 t/s, retired 10-30), `nemotron-bolt-e4b` (never
measured, retired 10-30), `kolibri` (78.1B, 60.5 t/s, 13/14 — an `reasoning_effort=none` arm on the same file also measured
HE 0.8293 (136/164 @512) and MMLU-Pro 0.4000 (48/120 @512), and is excluded from the matrix only
because it disables deliberation and its MMLU grader accepts refusal-shaped strings containing
the letter), `qwen38` (27.3B Q6_K, 8.8 t/s),
`qwen38fn` / `qwen38fn-upstream` (176.9B Q2_K, 29.6 / 42.9 t/s), `qwen38-27b-fable` (12.0 t/s),
`muse-glimmer` (10.9 t/s), `mellum21-12b-thinking` (28.0 t/s).

### 9.1 Per-model analysis

**gemma4-26b-uncen — the deployed driver, and the current ceiling.** 0.9573 code, 0.8500 MMLU, 14/14
riddles, 3/3 preflight, both needles, 56.9 t/s decode at 1759 t/s prefill, 15.6 GiB resident, 131k
context. Measured 2026-10-28 and serving since: `llama-gemma4-26b-uncen.service` on :8100 is the only
enabled model unit and it is what answers WhatsApp. It is the best HumanEval and the best MMLU-Pro on
disk, and the uncensoring costs nothing measurable — same architecture, same quant rung, same speed
class as the QAT file below.

**gemma4-26b-qat-q4 — the non-uncensored alternative.** One weight file, two runs: 0.9512 (156/164)
in the 2026-10-21 matched run and 0.9390 (154/164) in the 2026-10-17 run, MMLU 0.8417 (101/120) in
both, 59.5 t/s, 13.4 GiB resident, 131k context. Version 1.2 listed those two runs as two different
models; they are the same file. It keeps the :8099 script as the fallback if the uncensored weights
are ever distrusted, but its unit is disabled because :8100 already holds the channel slot.

**gemma4-26b-a4b Q8_0 — retired 2026-10-30, and its row was genuine.** It was re-measured on
2026-10-30 specifically to test a suspicion that its stored numbers had been borrowed from the
driver. They had not: 0.9573 (157/164) and 0.8667 (104/120) at cap 2048, reproducing the 2026-10-17
row item for item on a different kernel. It went on size and speed, not on distrust of the number —
the Q4_K_M posts 0.9573 and 0.8500 for 10.5 GiB less and 8 t/s more, and the difference is 2 items
(1.7 pp) against a 3.3 pp standard error. Its numbers stay in Table 4 because 0.8667 is the highest
knowledge score ever measured on this box.

**minicpm-v47-35b — the vision specialist.** 0.9573 code at a 4096 cap (second best on code, and
measured *above* the a4b), 0.7750 MMLU, 64.6 t/s, and it is multimodal with a 1.0 GiB projector. It
fails preflight 0/3 for a benign reason: its template expects image content and refuses bare chat
probes. Treat the 0/3 as a template artefact, not a quality signal — but do not wire it behind a
text-only agent interface either.

**ornith-122b — the best big model.** 124.6B at Q4_K_M (74 GiB), 0.9512 code, 0.7917 MMLU, 23.3 t/s
and 605 t/s prefill. This is the honest big-model result on Strix Halo: 74 GiB fits, it works, it is
slightly better on code than the 26B driver and clearly worse on speed. Its niche is difficult code
and long single-shot reasoning where 20 seconds of latency is acceptable.

**nemotron-super-120b — biggest and least ergonomic.** 123.6B at Q3_K_M, 0.9329 code, 0.7667 MMLU,
27.1 t/s but only 411 t/s prefill and the weakest instruction-following of the large models
(0.600/0.533). It is beaten by the 26B driver on knowledge and instruction, and by the 122B on
prefill. Kept because it is genuinely 120B-class and sometimes size alone matters, not because it
wins an axis.

**Nemotron-Bolt-74B-A9B at IQ2_XXS — retired 2026-10-30, kept as the quantisation warning.** 0.9451
code (excellent), 13/14 riddles, 72.8 t/s — and **0.3667 MMLU**, 44 of 120 items at 2.06 bits per
weight. The model retained procedural skill and lost factual knowledge almost entirely, and no
cap-4096 arm exists for this file, so the knowledge axis could not be recovered by budget. Its
sibling load at the same nominal quant (`nemotron-bolt` row) scored 0.1786 on code, i.e. it broke.
Two lessons survive the deletion: 2-bit quants can preserve one axis while destroying another, and
two files with the same recipe can behave completely differently.

**qwen3next-q6 — the reasoning generalist.** 79.7B Q6_K, 0.9207 code, 14/14 riddles, 45.8 t/s. Weak
knowledge (0.6058) but the best instruction-following of any large model here (0.885/0.923) and
perfect on the trap probes. The long-standing personal favourite for exactly this reason: it follows
instructions precisely at a usable speed. Retired from the driver seat only because the gemma QAT is
faster and stronger on knowledge.

**qwen3next-q4 — same family, three times the footprint, no gain.** Measured 2026-10-31, the first
capability row this file has ever had: 0.9146 code (150/164) and **0.7417 knowledge** (89/120) at cap
2048, 14/14 riddles, both needles, 3/3 preflight, 58.1 t/s decode at 1219 t/s prefill. Against the
driver that is −4.3 pp code and −10.8 pp knowledge for 42.9 GiB instead of 15.6 — at the same decode
speed. It also loses to gpt-oss-abliterated, an 18.7 GiB file, on both axes. The 80B/3B-active
architecture spreads its active experts too thin: it matches the Q6 sibling on code (0.9146 vs 0.9296
over 142 items, inside noise) but the knowledge axis shows what the extra 42 GiB of weights buys,
which is nothing. Retire candidate on evidence, not on opinion.

**mellum21-fork — the speed champion and best value.** 12.1B with 2.5B active, **111.9 t/s decode,
2723 t/s prefill**, 0.9146 code at an 8192 cap, 0.8083 MMLU. Nothing else on this box comes close on
throughput per byte, and 0.91 code from a 7.5 GiB file is remarkable. The catch is the 8192 cap: at
4096 it truncates mid-derivation and scores lower. It is also a fork-specific build. Use it for
high-volume, low-latency work — classification, extraction, triage — not for hard reasoning.

**lfm25-24b-a2b — the fastest 24B.** 106.6 t/s, 2930 t/s prefill, 24B with 2B active. Lower quality
(0.8537 code, 0.6917 MMLU) but the most responsive model of its size class, with a 1M-token context
option. Its IFEval 0.3333 in the archive is an lm-eval artefact; standalone at a 4096 cap it
measures 0.9333, which is one of the best instruction scores on the box.

**kimi (Kimi-Linear 48B-A3B) — retired 2026-10-29.** 67.4 t/s, a verified million-token window,
13/14 riddles, but 0.7866 code and 0.5500 knowledge. It was the only million-token model this box has
served; it went on footprint, not capability — 28 GiB for two axes both beaten by models a third its
size. Long-document work now uses LFM2.5's 1M option (§12).

**hy-memory-30b-a3b — retired 2026-10-29.** 74.7 t/s, 0.7805 code, 0.7250 MMLU, and a Q8 variant
that raised knowledge to 0.7500 while dropping to 52.3 t/s. Retired as a redundant 30B: 17 GiB for a
knowledge row 12.5 pp behind the 26B driver at two-thirds the speed. The Q4/Q8 pair remains the
cleanest quant-ladder datapoint in the archive (§10.3).

**qwen38-35b / qwen36-35b / ornith35b / Ornith-1.5-35B — the 35B trough.** All four land between
0.82 and 0.85 code with mediocre knowledge and 57-72 t/s. They are not bad; they are simply
dominated by the 26B MoE (faster and better) and the 122B (slower but much better).

`ornith35b` is the exception, and it was re-measured on 2026-10-31 to prove it: at **cap 4096** it
scores 0.5671 code (93/164) and 0.6333 knowledge (76/120), against 0.5610 / 0.6000 at cap 512. One
HumanEval item and four MMLU items — inside noise at those sample sizes. So the 512-token cap was
*not* truncating this model: an aggressive IQ3_XXS load on an IQ3-class file really is a ~0.57 coder,
and its riddles fell 13/14 → 12/14 when one arithmetic item (9.9 → 9.11) went wrong. The useful
conclusion is the reverse of the qwen38-35b case: a 512 cap sometimes hides capability, and sometimes
it tells you the truth, and only re-measuring distinguishes them.

**gptoss / gptoss-abliterated — the 120B MoE pair.** Both 116.8B MXFP4 at 59 GiB, both 0.9268 code
at ~50 t/s, riddles 12/14 and 10/14. Their knowledge rows are *not* comparable: the base was
measured at a 512-token cap and the abliterated build at 2048 (§16.2 shows the pair in full), so the
apparent 0.17 gap is a token budget, not the weights. Useful when you want 120B-class breadth at 50
t/s and can afford 59 GiB.

**qwen38fn-abl — the knowledge collapse.** 176.9B at IQ3_S: 0.8476 code, **0.0083 MMLU** (1 of 120).
Something is badly wrong with this quantisation — the model can write code but cannot answer a
multiple-choice question. Best example in the archive of why preflight-plus-MMLU belongs next to
HumanEval: a code score alone would have made this look like a 177B keeper.

**graft-50b-a3b — perfect riddles, ordinary code.** 14/14 when almost nothing else scores 14/14, but
0.7805 code and 0.6583 knowledge. A curiosity rather than a pick.

**Retired after measurement (recipes in `~/llama-local/RETIRED-models.md`).**

- **flint (40B-A2.5B)** — 0.9167 code (60-item subset), riddles 10/14, 60.4 t/s. Retired because the
  driver beats it on code, riddles and speed; its 262k context is already covered by Kimi-Linear. -
  **sage-a1.5** — 0.8659 code with thinking off; with thinking on, **20/20 code items failed** while
  burning the full 4096 cap at ~53 s each. Fixed by baking `enable_thinking:false` into the unit,
  but the model still did not take the driver slot. - **groot-19b-a3b** — 0.9333 on a 60-item subset
  only (unranked), riddles 8/14. - **REAP50 Ornith-122B (19.95 GiB)** — a genuinely pruned 122B (128
  experts vs 256) that was 1.6x faster and **failed preflight 1/3**: it repeated its JSON reply four
  times and argued with the one-word constraint. Its publisher reported 0.9390 code under
  reasoning-on/32768-cap/temp-0.6. - **Raon-1 mini (KRAFTON, 15 GiB)** — 0.9146 code, 0.7750 MMLU,
  8/14 riddles, 46.9 t/s, preflight 3/3, but requires a vendor fork to load at all. -
  **Spark-X2.6-4B (3.3 GiB)** — real 1,048,576 context (20 GiB KV, needle retrieved at 234,720
  tokens), 60.7 t/s, but 0.6833 code with 17 of 60 items cap-burned and no completed MMLU run. -
  **SenseNova U1.5 8B MoT** — never runnable: every public GGUF declares `arch = wan`, i.e. video
  diffusion weights, and llama.cpp has no converter for the real architecture.

**Retired on 2026-10-29 (61.6 GiB) and 2026-10-30 (245.1 GiB).** Every one has a full record —
removed paths, byte counts, sha256 per file and a restore URL — in `~/llama-local/RETIRED-models.md`.

- **gemma4-31b QAT Q4_0 (18.0 GiB)** — the all-time code leader (0.9634, 0.8667 MMLU, 14/14) and still
  the right thing to drop: dense 30.7B at 17.0 t/s, so a suite on it costs 2.5x the wall clock of any
  MoE at the same score, and for one item more than the 26B driver at a third of the speed. Shape and
  speed, not quality.
- **gemma4-26B-A4B Q8_0 (26.1 GiB)** — verified genuine by re-measurement on 10-30, then retired on
  size/speed: 2 items of knowledge for +10.5 GiB and -8 t/s against the Q4_K_M.
- **Ling-3.0-flash Q4_K_M (71.7 GiB)** — MMLU 0.7667 at cap 2048 was respectable, HumanEval never ran,
  and 77 GB of weights took the whole 100 GiB pool, meaning serving it silenced the driver.
- **Nemotron-Bolt-74B-A9B IQ2_XXS (23.1 GiB)** — 0.9451 code against 0.3667 knowledge at 2.06 bpw.
- **Flint-40B-A2.5B-abliterated i1-Q4_K_M (22.5 GiB)** — no capability row attributable to this file
  (a 60-item HumanEval probe only); the 0.7848 and 0.5167 seen under the alias `flint` belong to the
  earlier, differently-named FLINT artefact already retired on 10-24.
- **Swift Qwen3.8-Flash-Next IQ2_XS (63.5 GiB)** — capability never measured, and a lower-quant
  duplicate of the IQ3_S file :8097 still serves.
- **Huihui Coder390 IQ3_S1 (11.3 GiB)** — dense 27B, 16.3 t/s, and no capability row beyond riddles.
- **Nemotron-Bolt-E4B UD-Q8_K_XL (8.9 GiB)** — never measured.
- Earlier, on 10-29: **Kimi-Linear-48B-A3B (28.0)**, **Hy-Memory-30B-A3B (17.0)**, **Mellum2.1 Q6_K
  (10.1)** and its **MXFP4 twin (6.5)** — all measured, all beaten on their own axis by something
  smaller or faster.

---

---

## 10. Can you extrapolate from one model to another in the same family?

This is the question that decides how much of this document you can reuse. If results transferred
across a family, one careful measurement of a 26B model would tell you what to expect from its 31B
sibling, from its abliterated variant, and from its Q4 requantisation. They do not transfer
uniformly, and the pattern of where they fail is consistent enough to state as rules.

### 10.1 Four things "same family" can mean

The phrase is used for four different relationships, which is the root of most bad extrapolation:

```
   (a) SAME WEIGHTS, DIFFERENT ENCODING     gemma4-26b-qat-q4  vs  gemma4-26b-a4b
       only quantisation differs. The most predictable relationship on this box.

   (b) SAME BASE, DIFFERENT FINETUNE        gptoss  vs  gptoss-abliterated
       abliteration, distillation, uncensoring. Per-axis shifts, direction not
       predictable without measurement.

   (c) SAME FAMILY, DIFFERENT SIZE          gemma4-26b-*  vs  gemma4-31b
       ordering is usually preserved on knowledge and code; absolute numbers and
       speed are not.

   (d) SAME LINEAGE NAME, DIFFERENT ARCH    qwen35  vs  qwen36  vs  qwen38
       NOT a family for extrapolation. Different architectures that share a
       branding convention. Treat as unrelated models.
```
Any statement of the form "the X family scores about Y" silently assumes one of these and usually
means (c) while quoting evidence from (a). Distinguishing them is most of the work.

### 10.2 Measured spread inside each family

Computed from `~/runs/catalogue.json`, latest run per model, restricted to models that share weights
or a direct lineage. `Δ` is max − min within the family.

**Table 5 — Within-family spread on the measured axes.**

```
   family            n   HumanEval             MMLU-Pro              riddles    decode
   ──────────────────────────────────────────────────────────────────────────────────────────
   gemma4            4   0.9390-0.9634 Δ.024   0.8417-0.8667 Δ.025   14-14/14   17-59 t/s
   ornith / qwen3.5  6   0.5610-0.9512 Δ.390   0.4167-0.7917 Δ.375   11-13/14   23-73 t/s
   qwen3.6 / 3.8     7   0.8354-0.8537 Δ.018   0.0083-0.5083 Δ.500   11-13/14   53-68 t/s
   nemotron          3   0.1786-0.9512 Δ.773   0.3667-0.7667 Δ.400    8-13/14   23-73 t/s
   mellum            3   0.8780-0.9146 Δ.037   0.7000-0.8083 Δ.108   10-11/14   92-112 t/s
   gpt-oss           2   0.9268-0.9268 Δ.000   0.5833-0.7500 Δ.167*  10-12/14   50-50 t/s
   hy-memory  ✗      2   0.7683-0.7805 Δ.012   0.7250-0.7500 Δ.025   11-12/14   52-75 t/s
   ──────────────────────────────────────────────────────────────────────────────────────────
   Δ values are lower bounds on family variance: n is 2-7 and one run per model.
   * gpt-oss knowledge Δ is a token-budget artefact (512 vs 2048 caps), not lineage — see §16.2.
   ✗ = no member of that family is on disk today. The gemma4 count rose 3 → 4 because the 26B is
   counted at both its Q4 encodings (QAT Q4_0, uncensored Q4_K_M) plus the Q8_0 baseline and the 31B;
   the nemotron ceiling is now nemotron-super-120b's 0.9512 rather than the 74B's 0.9451.
   The qwen3.6/3.8 knowledge spread of 0.500 rests on qwen38fn-abl's 1/120, which §8 and the figure
   §19.6 both treat as a poisoned cell and exclude; on valid rows that family's knowledge spread is
   0.058 (0.4500-0.5083). The table keeps the wider number because it is what the archive contains,
   and the footnote exists so nobody quotes 50pp as a lineage finding.
```
### 10.3 What the spreads establish

**Code is the one axis that survives family extrapolation — but only at comparable quantisation.**
The two dense families that were *not* damaged by quantisation show a spread of 1.8-2.4pp:
qwen3.6/3.8 across seven models from 0.8354 to 0.8537, gemma4 across three from 0.9390 to 0.9634. If
you know one member of such a family scores 0.94 on HumanEval, a sibling at the same quant is very
likely within ±3pp. That is a usable prediction.

**Knowledge is the axis where the confounds live, which is not the same as being fragile.** The two
double-digit spreads in Table 5 — gpt-oss at 16.7pp and qwen3.6/3.8 at 50pp — are a token-budget
difference and a 3.4-bit quantisation respectively, not lineage (§16.2 shows the gpt-oss pair in
full). Where caps and quants *are* matched the picture is calm: gemma4's three models sit 2.5pp
apart on knowledge and hy-memory's Q4/Q8 pair 2.5pp apart, both at identical caps. So the honest
rule is narrower than "knowledge never transfers": knowledge transfers **between variants measured
the same way**, and it is the axis most easily corrupted by a cap change, a quant rung or a
finetune. Check those three before attributing a knowledge gap to the family at all.

**The 0.39 and 0.77 spreads are not family variance at all.** They are quantisation and load
failures inside the group: `ornith35b` at IQ3_XXS (0.5671, cap 4096) against `ornith-122b` at Q4_K_M (0.9512),
and `nemotron-bolt` (0.1786, a broken load) against `Nemotron-Bolt-74B` at IQ2_XXS (0.9451). This is
the central trap. A "same family" comparison that spans quantisation levels measures the encoder,
not the lineage, and it will happily produce a 0.77 spread that has nothing to do with the models'
design.

**Speed never transfers.** gemma4 spans 17-59 t/s and hy-memory spans 52-75 t/s within families.
Decode rate is set by active parameters, quantisation and build flags — 'family' predicts none of
them. If you need a throughput estimate, measure it or compute it from bytes-per-token; do not infer
it from a sibling.

**Instruction adherence and preflight do not transfer either.** These are properties of the chat
template and the post-training recipe, both of which change between variants. One measured case: the
REAP50 pruning of Ornith-122B kept a respectable code score and failed two of three preflight probes
while its base passed all three. A model that is a good agent is not evidence that its siblings are.

### 10.4 Rules of extrapolation

Figure 10 — What extrapolates and what does not.

```
   ┌──────────────────────────────────────────────────────────────────────────────┐
   │ SAFE      ordering within a family at a FIXED quantisation                   │
   │           ("the 31B will beat the 26B on knowledge")                          │
   │                                                                              │
   │ RISKY     absolute code scores across (a)-type relationships                 │
   │           (QAT vs post-hoc, UD vs plain K-quant): ±1-2pp typically,           │
   │           but the sign is not guaranteed — smaller quantised better twice     │
   │           in four measured pairs                                             │
   │                                                                              │
   │ UNSAFE    knowledge across finetunes, abliterations and ≤3 bpw               │
   │           measured failures: −16.7pp inside gpt-oss, −50pp inside qwen3.8     │
   │                                                                              │
   │ UNSAFE    decode/prefill speed, always                                      │
   │                                                                              │
   │ UNSAFE    preflight and instruction adherence, always                        │
   │                                                                              │
   │ NEVER     across (d)-type "families" — qwen35/36/38 are not relatives        │
   └──────────────────────────────────────────────────────────────────────────────┘
```
The one-line version: **extrapolate rankings within a family at one quantisation level; never
extrapolate absolute scores, speed, or instruction behaviour.** If a decision depends on the number
rather than the ordering, measure the number.

### 10.5 Threats to validity

An honest account of what these results cannot support, because the same caveats apply to anyone
reading them as a benchmark:

- **n = 1 run per model per axis.** No seed variance, no repeated runs, no confidence intervals. The
  HumanEval means carry ~1.3pp standard error at 164 items and ~3.5pp at 60; MMLU-Pro ~3.9pp at 120.
  Rankings separated by less than those margins are not established. - **Temperature 0 throughout.**
  Deterministic, reproducible, and not how the models will be used. Some models' instruction
  adherence degrades at temperature; this document would not see it. - **One machine, one build
  lineage.** Vulkan on gfx1151 with a specific llama.cpp build. Scores are hardware-robust in a way
  speeds are not, but kernel-specific numerical differences are unmeasured. - **Caps differ between
  rows** (512-8192). This is the largest single source of misleading comparisons in the tables,
  which is why §7.3 exists and why every score in this document carries its cap. - **Family samples
  are tiny.** n = 2-7. The Δ values in Table 5 are observed spreads, i.e. lower bounds; the true
  variance of a family is at least that and probably larger. - **Selection effects.** These models
  were not sampled randomly — they were chosen because they looked promising, which biases every
  family's apparent quality upward relative to the open population.

## 11. League tables

The same measurements as §9, sorted one axis at a time, so that a single capability can be read
without the others getting in the way.

### Code — HumanEval

```
  0.9634  cap 2048  gemma4-31b                        ✗ retired 10-30 (all-time leader)
  0.9573  cap 4096  minicpm-v47-35b                  <- best on disk, with gemma4-26b-uncen
  0.9573  cap 2048  gemma4-26b-uncen                 <- deployed driver
  0.9573  cap 2048  gemma4-26b-a4b Q8_0              ✗ retired 10-30
  0.9512  cap 2048  gemma4-26b-qat-q4
  0.9512  cap 4096  ornith-122b
  0.9512  cap 4096  nemotron-super-120b              (156/164; the other run reads 154/164)
  0.9451  cap 2048  Nemotron-Bolt-74B-A9B (IQ2_XXS)  ✗ retired 10-30
  0.9296  cap  —    qwen3next-q6                     [142 items]
  0.9268  cap 2048  gptoss · gptoss-abliterated
  0.9242  cap  —    qwen35                           [66 items only] ✗
  0.9207  cap 4096  ornith-mtp-21g
  0.9167  cap 4096  flint i1-Q4_K_M                  [60 items] ✗ retired 10-30
  0.9146  cap 8192  mellum21-fork
  0.9146  cap 2048  qwen3next-q4              [loses to an 18.7 GiB file on both axes]
  0.8780  cap 4096  mellum                           ✗ retired 10-29
  0.8537  cap  512  qwen38-35b                       <- floor estimate
  0.8537  cap 4096  lfm25-24b-a2b
```
### Knowledge — MMLU-Pro

```
  0.8667  cap 2048  gemma4-31b                        ✗ retired 10-30 (all-time leader)
  0.8667  cap 2048  gemma4-26b-a4b Q8_0              ✗ retired 10-30
  0.8500  cap 2048  gemma4-26b-uncen                 <- best on disk; deployed driver
  0.8417  cap 2048  gemma4-26b-qat-q4
  0.8083  cap 8192  mellum21-fork                    <- 8192 cap: upper bound
  0.7917  cap 4096  ornith-122b
  0.7750  cap 4096  minicpm-v47-35b
  0.7750  cap 2048  ornith-mtp-21g
  0.7667  cap 4096  nemotron-super-120b
  0.7667  cap 2048  Ling-3.0-flash                    ✗ retired 10-30
  0.7500  cap 2048  gptoss-abliterated
  0.7500  cap 2048  hy-memory-30b-a3b-q8             ✗ retired 10-29
  0.7417  cap 2048  qwen3next-q4                     <- 80B of weights, 15.6 GiB driver beats it by 10.8 pp
  0.7250  cap 2048  hy-memory-30b-a3b                ✗ retired 10-29
  0.7000  cap 4096  mellum                            ✗ retired 10-29
  0.6917  cap 4096  lfm25-24b-a2b
  0.6058  cap  —    qwen3next-q6
  0.5833  cap  —    gptoss
  0.5500  cap 2048  kimi                              ✗ retired 10-29
  0.3667  cap 2048  Nemotron-Bolt-74B-A9B             ✗ 2-bit knowledge collapse
  invalid cap 2048  qwen38fn-abl                      <- 1/120, a poisoned cell not a score
```
### Instruction following — IFEval (prompt-strict / inst-strict)

```
  0.9167/0.9500  n=12  qwen35                                   ✗
  0.9000/0.9333  n=30  gemma4-31b                               ✗ retired 10-30
  0.8846/0.9231  n=26  qwen3next-q6                             <- best on disk
  0.8667/0.9111  n=30  qwen38-35b · qwen36-35b                   (qwen36 ✗)
  0.8333/0.8889  n=30  gemma4-26b-a4b (the Q8_0 file, ✗) · gemma4-26b-uncen (driver)
  0.8000/0.8667  n=30  gemma4-26b-qat-q4 · gptoss · Ornith-1.5-35B   (Bolt-74B ✗)
  0.7667/0.8000  n=30  gptoss-abliterated
  0.7333/0.8222  n=30  ornith-122b
  0.7333/0.6444  n=30  mellum                                   ✗ retired 10-29
  0.6000/0.5333  n=30  nemotron-super-120b
  0.3333/0.2889  n=30  lfm25-24b-a2b     <- lm-eval 1280-token artefact; 0.9333 standalone
```
### Reasoning — riddles + arithmetic (/14)

```
  14/14  gemma4-26b-qat-q4 · gemma4-26b-uncen · qwen3next-q6 · qwen3next-q4 · Ornith-1.5-35B  [on disk]
  14/14  gemma4-26b-a4b Q8_0 ✗ · gemma4-31b ✗ · graft-50b-a3b ✗
  13/14  qwen38-35b · kolibri · qwen38fn-upstream        (kimi ✗, Bolt-74B ✗)
  12/14  gptoss · ornith-122b · ornith35b (boot)                     (hy-memory ✗, qwen35 ✗, qwen36 ✗)
  11/14  nemotron-super-120b · ornith-mtp-21g · qwen38fn-abl        (mellum ✗, hy-memory-q8 ✗)
  10/14  lfm25-24b-a2b · minicpm-v47-35b · mellum21-fork · gptoss-abliterated
   8/14  nemotron-bolt ✗
```
### Throughput

```
  decode t/s      prefill t/s   model
   111.9            2723        mellum21-fork
   106.6            2930        lfm25-24b-a2b
    91.8            2442        mellum                          ✗ retired 10-29
    74.7            1515        hy-memory-30b-a3b               ✗ retired 10-29
    72.8             577        Nemotron-Bolt-74B-A9B           ✗ retired 10-30
    72.5            1629        Ornith-1.5-35B
    69.9            1762        ornith35b (uncensored, boot)
    68.3            1560        qwen38-35b
    67.4            1597        kimi                            ✗ retired 10-29
    65.2            1610        ornith-mtp-21g
    64.6            1600        minicpm-v47-35b
    60.5            1297        kolibri
    59.5            1624        gemma4-26b-qat-q4
    56.9            1759        gemma4-26b-uncen                <- driver, enabled
    48.9            1900        gemma4-26b-a4b Q8_0             ✗ retired 10-30
    27.1             411        nemotron-super-120b
    23.3             605        ornith-122b
    17.0             350        gemma4-31b                      ✗ retired 10-30
```
### The only table that decides anything

Models clearing **all three** quality bars (code ≥ 0.92, knowledge ≥ 0.75, riddles ≥ 13):

```
  HE 0.9573  MMLU 0.8500  14/14  56.9 t/s   gemma4-26b-uncen   <- driver (Q4_K_M)
  HE 0.9512  MMLU 0.8417  14/14  59.5 t/s   gemma4-26b-qat-q4        (Q4_0, unit disabled)
```
Two models, one architecture, on two weight sets — and until 2026-10-30 there was a third (the 31B at
0.9634 / 0.8667, 17 t/s) which lost its place on shape and speed rather than score. That is still the
real shape of the roster: gemma4 owns breadth, and every other model on disk is a specialist that
wins exactly one axis — minicpm on vision, ornith-122b on generous-cap code, gptoss on 120B breadth,
mellum21 on throughput, qwen3next-q6 on instruction adherence.

---

## 12. Which model for which job

The point of measuring axes separately is that they do not correlate. Below, each job maps to the
axis that actually governs it, and to the model that wins that axis *while still being usable*.

Figure 11 — Routing a job to the axis that governs it, then to a model.

```
                        ┌─────────────────────────┐
                        │  what is the job?       │
                        └───────────┬─────────────┘
                                    │
        ┌───────────────┬───────────┼────────────┬────────────────┐
        ▼               ▼           ▼            ▼                ▼
   interactive?     hard code?  know things?  long doc?      images?
        │               │           │            │                │
        ▼               ▼           ▼            ▼                ▼
   latency rules   HumanEval    MMLU-Pro     1M ctx          vision
        │           + riddles                  + retrieval
        ▼               ▼           ▼            ▼                ▼
   gemma4-26b-     minicpm-v47  gemma4-26b   lfm25-24b-a2b   minicpm-v47
   uncen (56.9)    ornith-122b  uncen        (1M ctx; kimi   -35b
   or mellum21     (64 / 23)    (0.8500)     retired 10-29)  (64.6 t/s)
   (111.9)
```
**Table 6 — Job to axis to model.**

| Job | Axis that governs it | Use | Why |
|---|---|---|---|
| Chat / agent behind a messaging channel | preflight + decode speed + riddles | **gemma4-26b-uncen** | 3/3 preflight, 56.9 t/s, 14/14 traps, 15.6 GiB and it is already the enabled unit on :8100 · non-uncensored fallback **gemma4-26b-qat-q4** |
| Difficult one-shot code | HumanEval at a generous cap | **minicpm-v47-35b** or **ornith-122b** | 0.9573 at cap 4096 / 0.9512 at cap 4096; the 0.9634 gemma4-31b that used to hold this slot was retired 10-30 for being dense and 17 t/s — latency is irrelevant for a single answer, so it is the one job it was still defensible for |
| Bulk classification, extraction, triage | decode speed + instruction strictness | **mellum21-fork** (111.9 t/s) or **lfm25** (106.6) | throughput dominates; both follow short instructions well when given room |
| Document Q&A over 100k-1M tokens | context + retrieval, not knowledge | **lfm25-24b-a2b (1M ctx)** | the 1M option survives on the only model of that class still on disk; Kimi-Linear, which held this slot with a verified million-token window, was retired 2026-10-29 |
| Vision: describe, OCR-adjacent, camera frames | multimodal + prefill | **minicpm-v47-35b** | 0.9573 code at 4096 and a 1 GiB projector at 64.6 t/s; the only strong VLM measured |
| Reference answers / offline judging | MMLU + HumanEval | **gemma4-26b-uncen** | 0.8500 MMLU and 0.9573 code are the best on disk; the 31B that led both axes (0.8667 / 0.9634) went on 10-30 and its numbers remain as the all-time reference |
| Long agent loops with many tool calls | instruction-following + riddles | **qwen3next-q6** | 0.885/0.923 IFEval and 14/14 traps; best constraint adherence of the large models |
| 120B-class breadth at speed | capacity + decode | **gptoss / gptoss-abliterated** | 116.8B at 59 GiB and ~50 t/s; the abliterated build matches it on code at the same speed |
| Unrestricted / uncensored work | capacity + compliance | **gemma4-26b-uncen** (small/fast) or **gptoss-abliterated** (120B breadth) | the gemma is the uncensored build already in the channel slot at 56.9 t/s; the gpt-oss twin matches its base on code and its knowledge row is cap-confounded, not superior (§16.2) |
| Largest model, cost no object | parameters | **nemotron-super-120b** | 123.6B; weakest instruction adherence of the big models, so use it for single-shot work |
| Fast long-context utility | context + speed | **lfm25-24b-a2b (1M ctx)**, now that Spark is retired | 106.6 t/s with a million-token window |

Three anti-patterns this matrix is designed to prevent:

1. **Putting the smartest model in front of the chat channel.** gemma4-31b was the best model on the
   box and the worst choice for a messaging channel: 17 t/s and 350 t/s prefill meant the reply
   arrived long after the user had moved on — which is why the channel is served by a 26B MoE at
   56.9 t/s that gives up 0.0067 on code for 3.3x the decode rate. 2. **Judging a vision model by preflight.** minicpm fails 0/3
   and is still the right answer for images. The gate tests chat-shaped behaviour, which is not what
   a VLM is for. 3. **Assuming bigger is better on every axis.** The 122B and 120B models are beaten
   on knowledge by a 26B model and on instruction-following by a 79B one. Capacity buys capability
   only on the axis where the task is actually hard.

---

## 13. Strix Halo against Nvidia and Apple

The question that matters to a buyer is not which chip is fastest, but which constraint binds first:
capacity, bandwidth, or software ecosystem.

### 13.1 The three architectures side by side

Figure 12 — Three platforms side by side.

```
                       STRIX HALO           NVIDIA (RTX 4090/5090)      APPLE (M-series Max/Ultra)
   ─────────────────────────────────────────────────────────────────────────────────────────────
   Memory               128 GB unified         24 / 32 GB VRAM            64-512 GB unified
   GPU-addressable      ~100 GiB (GTT)         = VRAM, hard wall          ~75% of RAM by default
   Bandwidth            ~256 GB/s              ~1008 / ~1792 GB/s         ~546 GB/s (Max)
                                                                           ~819 GB/s (Ultra)
   Compute              RDNA 3.5, 40 CU        CUDA cores + tensor        Apple GPU + Neural Engine
                        no tensor cores        cores, best in class       no CUDA
   Software             Vulkan + llama.cpp     CUDA: vLLM, TRT-LLM,       Metal + MLX: excellent
                        ROCm partial           FA, bitsandbytes, ...      for llama.cpp/MLX
   Power (whole box)    ~45-120 W              ~450-575 W GPU alone       ~40-140 W
   Price for 100 GB+    ~one laptop           4x 3090 or A100/H100       M3 Ultra 512 GB: premium
   ─────────────────────────────────────────────────────────────────────────────────────────────
```
### 13.2 What the numbers mean in practice

**The capacity wall is the real dividing line.** A 128 GB Strix Halo runs a 120B model at Q4 and a
74 GiB model comfortably. A 24 GB RTX 4090 cannot run either; it tops out around 30B at Q4, and a
70B model requires two cards with tensor-parallel plumbing. If your goal is "run the biggest open
models locally", unified memory is the cheap path and discrete VRAM is the expensive one.

**Bandwidth is the price you pay for that capacity.** Decode speed is roughly bandwidth divided by
bytes read per token. This box reads 13.4 GiB per token for its driver at 59.5 t/s; a 4090 with
roughly 4x the bandwidth would decode the same model 3-4x faster *if the model fit*, which for
anything above ~30B it does not. The comparison only becomes fair when you compare models that fit
on both machines, and at that point the Nvidia card is 3-4x faster per token and the Strix box runs
models the card cannot hold at all.

**Prefill is where Strix Halo is genuinely weak.** No tensor cores means prompt processing runs at
350-2900 t/s versus several thousand to tens of thousands on modern Nvidia parts. For chat with
short prompts this is invisible. For an agent pushing 30k-token contexts it is the difference
between a 2-second and a 60-second wait. If your workload is long-prompt-heavy, this is the wrong
machine and no amount of model choice fixes it.

**Apple sits between them.** M-series Max/Ultra have unified memory *and* high bandwidth (546-819
GB/s), with Metal and MLX being genuinely good, mature paths for local inference. An M4 Max with 128
GB will decode the same model roughly 2x faster than this box. What it does not have is CUDA, so the
Nvidia-specific ecosystem is equally unavailable, and it does not have upgradeable RAM or a
user-serviceable OS. It is the better *appliance*; the Strix box is the better *laboratory*.

### 13.3 Choosing between them

Figure 13 — Choosing a platform.

```
   ┌────────────────────────────────────────────────────────────────────────────┐
   │ Pick NVIDIA if ...                                                         │
   │   • you need maximum tokens/second and your models fit in 24-32 GB         │
   │   • you need vLLM, TensorRT, CUDA kernels, training or fine-tuning         │
   │   • you are serving multiple concurrent users                              │
   │   • power, heat and noise are not your problem                             │
   ├────────────────────────────────────────────────────────────────────────────┤
   │ Pick APPLE if ...                                                          │
   │   • you want a quiet, efficient, appliance-like box with unified memory    │
   │   • you live in the MLX / Core ML ecosystem or want the best laptop UX     │
   │   • 64-192 GB is enough and you value battery, silence and resale value    │
   │   • you are prepared to pay a premium per GB of RAM                        │
   ├────────────────────────────────────────────────────────────────────────────┤
   │ Pick STRIX HALO if ...                                                     │
   │   • you want the most GPU-addressable memory per currency unit             │
   │   • you run Linux and are comfortable building llama.cpp from source       │
   │   • your loads are chat, extraction, code, vision — not long-prompt agent  │
   │   • you want a 24/7 box that idles at a few watts and serves several jobs  │
   └────────────────────────────────────────────────────────────────────────────┘
```
The honest summary: **Strix Halo buys capacity, Apple buys capacity with bandwidth, Nvidia buys
throughput.** This box is the cheapest way to hold 100 GiB of model in GPU address space, and it is
the wrong choice if your bottleneck is prompt processing or concurrent throughput rather than model
size.

---

---

## 14. Hosted frontier models as a reference point

Everything up to here answers "which model should this machine run". This section answers a
different question, and it is the one a buyer asks first: **how far behind is a local model on this
box, and what does closing the gap cost?**

Four hosted models were measured with the same harness, the same prompts, the same caps and the same
scoring as the local roster. They are not roster members and do not appear in the league tables —
the comparison is between *systems*, not weights, and mixing them into a per-axis ranking would
invite exactly the cross-context ranking §8 forbids.

### 14.1 Method, and what is and is not equalised

The harness speaks HTTP to `127.0.0.1:<port>` and reads llama.cpp's `timings` block. Hosted models
are reached through `~/bench/api-shim.py`, a ~150-line proxy that forwards to an OpenAI-compatible
endpoint, streams the reply so time-to-first-token is measurable, and synthesises that block.

```
   equalised                          not equalised
   ─────────────────────────────      ────────────────────────────────────────────────
   prompts, item order                serving hardware (provider GPUs, not this iGPU)
   generation cap (4096)              quantisation (BF16/FP8 and unknown per provider)
   temperature 0                      hidden serving configuration, safety layers
   scoring (exec, exact, JSON)        throughput magnitude (network + provider, not local decode)
   item counts 164 / 120 / 14         cost model (per token vs electricity)
   measurement date                   reproducibility (providers update models behind aliases)
```
Model identifiers were pinned where a dated snapshot exists: `deepseek/deepseek-v4.1-flash-1017`
resolves to canonical slug `deepseek-v4.1-flash-20261017`. The unpinned
`deepseek/deepseek-v4.1-flash` is a different route at a different price, and is reported
separately.

### 14.2 Results

**Table 7 — Hosted models against the local roster: same harness, same caps.**

```
   model                          HE(164@4096)  MMLU(120)  riddles  preflight  ttft   decode*
   ──────────────────────────────────────────────────────────────────────────────────────────
   anthropic/claude-sonnet-5.5    0.9756 (160)  0.9250     14/14    3/3        2.28s   229 t/s
   anthropic/claude-haiku-5.5     0.9756 (160)  0.7583     14/14    3/3        1.50s   377 t/s
   deepseek/deepseek-v4.1-flash-1017
                                  0.9512 (156)  0.8917     12/14    3/3        1.23s   749 t/s
   deepseek/deepseek-v4.1-flash   0.9207 (151)  0.9167     11/14    3/3        1.27s   257 t/s
   ──────────────────────────────────────────────────────────────────────────────────────────
   LOCAL reference points
   gemma4-26b-uncen (driver)      0.9573 (164)  0.8500     14/14    3/3        ~1.0s   56.9 t/s
   minicpm-v47-35b (VLM)          0.9573 (164)  0.7750     10/14    0/3        ~1.1s   64.6 t/s
   ornith-122b (124.6B)           0.9512 (164)  0.7917     12/14    3/3        ~3.0s   23.3 t/s
   gemma4-31b (30.7B dense) ✗     0.9634 (164)  0.8667     14/14    3/3        ~5.1s   17.0 t/s
   ──────────────────────────────────────────────────────────────────────────────────────────
   * hosted decode is provider GPU plus network and is NOT comparable in magnitude with
     local decode; it is shown to establish that these are fast systems, not to rank them.
     The figures come from the forced-400-token probe. The harness's own perf axis, which
     asks for 128 tokens, read 407 t/s on the pinned DeepSeek route against 749 t/s in the
     longer probe: short answers understate hosted decode, so treat this column as a floor.
```
### 14.3 Five findings

**1. Code is saturated. The local box is at statistical parity with the frontier.** Sonnet and Haiku
both score 0.9756 (160/164); the best local model scores 0.9634 (164 items). That is a 1.2pp gap
against a standard error of ~1.3pp at n=164 — inside the noise. Put plainly: on HumanEval, at these
caps, a 30B dense model on a desk-side box is **not measurably worse** than a hosted frontier model.
Anyone buying this hardware primarily to write code should know that the marginal quality gain from
the API is small.

**2. Knowledge is where the frontier separates — and the cheap tier does not.** Sonnet reaches
0.9250 MMLU-Pro against the best local score currently on disk, 0.8500 (gemma4-26b-uncen) — and 0.8667
for the retired gemma4-31b — a 5.8-7.5pp gap that is well outside the ~3.9pp standard
error at n=120. But **Haiku 5.5 scores 0.7583: 9.2pp below the current local driver (gemma4-26b-uncen,
0.8500) and below even the retired gemma4-31b (0.8667).** "Frontier" is not a property of a vendor's family, it is a property of a
model tier: the cheap hosted tier loses to a local 30B on factual knowledge while beating it on
code. That single row is the best argument in this document for measuring rather than assuming.

**3. Two routes for one model disagree — and not in the same direction.** The pinned and unpinned
DeepSeek V4.1 Flash routes are the same model family, and they split: the pinned snapshot is
stronger on code (0.9512 vs 0.9207) while the unpinned route is stronger on knowledge (0.9167 vs
0.8917) at a fifth of the input price and with 97.7% prompt caching. Nothing in the weights explains
that; the routes differ in serving configuration. It is the cleanest illustration in this document
that a hosted row describes a deployment.

**4. The hosted mid-tier is the value outlier.** DeepSeek V4.1 Flash (pinned) scores 0.9512 on code
— exactly the local 122B's score — and 0.8917 on knowledge, which is **+10pp over the local 122B and
+2.5pp over the best local model of any size**, at $0.02/$1.00 per Mtok. It also produced 12/14 on
the traps, matching the local 122B. If the workload is knowledge-heavy rather than latency-critical,
this is the strongest quality-per-currency result measured anywhere in this document — including the
local roster, whose marginal cost is electricity but whose quality ceiling is 0.8667.

**5. Reasoning tokens are billed and invisible.** The pinned DeepSeek route reported 24% of its
output tokens as reasoning; Haiku 10%; Sonnet and the unpinned DeepSeek route 0%. Two consequences:
the caps in this table are not comparable in *effective* budget between models, and a per-token
price list understates the cost of a reasoning model by roughly the reasoning share.

The cap-burn counts make the same point from the other side: **Haiku and Sonnet burned zero items**
at the 4096 cap on either axis, while the pinned DeepSeek route burned **4 of 164** on code and **7
of 120** on knowledge, and the unpinned route **11 and 6**. So the DeepSeek rows are, if anything,
slightly understated — their scores were earned with less room than the Claude rows had, and the
same 4096 cap does not buy the same amount of answer from each route.

### 14.4 Cache effectiveness, and why the price list is not the cost

A repeated prompt prefix can be served from cache. Whether that happens is a property of the
*route*, not the model, and the measured spread is large enough to invert the price list:

**Table 8 — Prompt-cache behaviour on identical repeated prefixes (~6-8k tokens, 4 calls each).**

```
   route                          cold call   repeat calls   cached share   cost per repeat call
   ──────────────────────────────────────────────────────────────────────────────────────────
   deepseek-v4.1-flash (alias)    $0.00063    $0.00004       97.7%          94% cheaper than cold
   deepseek-v4.1-flash-1017       $0.00192    $0.00192        0%            full price every call
   anthropic/claude-haiku-5.5     $0.00081    $0.00081        0%            full price every call
   anthropic/claude-sonnet-5.5    $0.01643    $0.01643        0%            full price every call
   ──────────────────────────────────────────────────────────────────────────────────────────
```
The measured cost of one complete sweep (core axes + HumanEval 164 + MMLU-Pro 120), 2026-10-26:

```
   claude-haiku-5.5              $0.06
   deepseek-v4.1-flash           $0.14
   deepseek-v4.1-flash-1017      $0.20
   claude-sonnet-5.5             $0.85
   all four together             $1.25
```
That is the whole comparison, at full item counts, for about the price of a coffee — which reframes
the cost objection. The asymmetry is not that hosted inference is expensive per sweep; it is that
hosted cost scales with every future call, while the local model's cost was paid once at purchase.

The route that caches is also the route that scored 0.9207 on code against the snapshot's 0.9512 —
so cheap-per-call and strong-on-code do not coincide here. Read the two tables together: prefer the
pinned snapshot when code quality decides, the unpinned route when prompt reuse dominates.

One further detail from the same probe, which matters for how caching is sold: on the route that
caches, the 97.7% hit rate cut cost per call from $0.00063 to $0.00004 — a 94% saving — while
time-to-first-token did **not** fall (1.45s cold against 1.84s averaged over the warm calls). So
prompt caching here is a billing optimisation, not a latency one: the prefix is not re-billed, but
the request still waits. Treat "caching enabled" as a cost claim until a latency measurement says
otherwise.

Two notes that matter for budgeting. First, the route with the *higher* headline input price ($0.11
vs $0.02 per Mtok) is the one that caches, so a prompt-reuse workload costs less on it — the nominal
price list ranks them the wrong way round. Second, the two Claude tiers report no automatic caching
at all on this route: Anthropic's caching requires explicit cache breakpoints in the request, which
a generic OpenAI-compatible shim does not emit. A harness that resends a long system prompt would
therefore pay full price for every call, where a local model pays nothing because the prefix stays
in its KV cache.

This is the mirror image of the local situation. Locally, prompt caching is free and automatic
(`cache_prompt`), and its cost is RAM. On a hosted route it is a billing feature that may or may not
be enabled, and it can move per-call cost by an order of magnitude.

### 14.5 Determinism and latency

Five identical calls at temperature 0 returned the identical answer on all four routes (the
bat-and-ball trap, `0.05`, every time). Hosted temperature-0 inference is reproducible in practice,
which is worth stating because it is often assumed otherwise.

Latency, measured with a forced 400-token answer so that buffering cannot masquerade as fast
streaming:

```
   deepseek-v4.1-flash-1017   ttft 1.23s   decode 749 t/s
   claude-haiku-5.5           ttft 1.50s   decode 377 t/s
   claude-sonnet-5.5          ttft 2.28s   decode 229 t/s
   deepseek-v4.1-flash        ttft 1.27s   decode 257 t/s

   local driver (gemma4-26b-qat-q4)   ttft ~1.1s at short prompt, 59.5 t/s decode,
                                      and 0.8s -> 515s as the prompt grows to 235k tokens
```
The honest reading: a hosted model's *first token* arrives in about the same time as the local
driver's, because network latency and local prefill happen to be similar at short prompts. The
hosted model then generates 4-13x faster. **But** the local driver's decode rate does not depend on
how many other users exist, its cost does not scale with use, and at long context the hosted models'
advantage in latency narrows sharply while their per-token cost keeps climbing.

### 14.6 Threats to validity specific to this comparison

- **Unknown quantisation and serving stack.** A hosted score describes a system the reader cannot
  inspect. The local rows can be reproduced exactly; the hosted rows cannot. - **Provider drift.**
  Pinned snapshots are stable; aliases are not. Every hosted row carries a date for this reason, and
  any re-read months later should be treated as a new measurement. - **Effective budget differs by
  reasoning share** (0-24% measured), so a fixed 4096 cap is not the same amount of *answer* budget
  across rows. - **Cost is not comparable to local cost.** Local marginal cost per sweep is
  electricity plus wear; hosted cost is per token and per cache behaviour. A like-for-like
  comparison would need the box's power draw over the run, which was not instrumented here. -
  **Selection.** The four hosted models were chosen because they are the plausible reference points
  for this workload, not because they are the strongest available at any price. - **n = 1 run per
  axis**, as throughout. Differences under ~1.3pp (HE) and ~3.9pp (MMLU) are not established.

### 14.7 What would change the recommendation

The local roster is defensible today because code — the axis where the gap is measurably zero — is
also the axis this box is used for most. Three things would move that:

1. **A knowledge-heavy workload.** The +5.8pp (Sonnet) or +10pp (DeepSeek over the local 122B) gap
   on MMLU-Pro is real and outside noise. If factual recall dominates, the API is worth its price.
   2. **A privacy or availability requirement.** Every hosted number here assumes the network and a
   third-party account are acceptable. For a WhatsApp channel that must answer while travelling, the
   local model's failure mode is "slow"; a hosted model's failure mode is "offline". 3. **A cheaper
   pinned snapshot with caching.** The DeepSeek route demonstrates that quality near the frontier is
   available at $0.02/Mtok with 97% cache hits. If that combination persists, the economics of
   keeping a 26B model resident for knowledge work rather than code needs revisiting.

---

---

## 15. What a local run costs in power, heat and money

§14 established what a hosted sweep costs in dollars. This section measures the other side of the
ledger: what a local sweep costs in watts, watt-hours and degrees, using the hardware monitor that
has been recording this machine continuously.

### 15.1 Where the numbers come from

The the hardware monitor service samples the board about once a second into a SQLite database
(`~/.local/state/the hardware monitor/history.db`, ~19.5 million samples). Four sensors matter here:

```
   CPU Package Power      W   the whole package — cores, memory controller and the integrated GPU
   GPU Power (PPT)        W   reported separately, but on this APU it tracks the package sensor
                               almost exactly: one silicon power domain, two telemetry paths.
                               Do NOT add the two columns together.
   CPU Tctl/Tdie          °C  the CPU thermal control point
   GPU Temperature        °C  edge temperature of the iGPU
```
Each run window was reconstructed from the axis log's modification time minus its recorded wall
clock, so the window is the run itself rather than a guess. Coverage is limited to 2026-10-23 onward
— the database was created then — which is why the rows below are the recent runs rather than the
full archive.

### 15.2 Idle against load

```
   CPU package power across 16,936 one-minute rollups
     p10    5.8 W      p25    6.0 W      median  6.4 W        <- idle, driver resident
     p90   94.3 W      p99  102.6 W      max    112.0 W        <- full local inference

   A local model generating tokens draws 15-18x its idle power. Idle is genuinely cheap:
   6 W continuous is ~53 kWh/year, roughly £13 at £0.25/kWh.
```
### 15.3 Per-run cost

**Table 9 — Power, energy and thermals for the measured local runs.**

```
   run                          wall    package W        Wh    Tctl peak   GPU peak
                                       mean / peak
   ─────────────────────────────────────────────────────────────────────────────────
   Raon-1 mini, core axes        668s   88.9 / 118.4    16.5     72.6 °C    75.0 °C
   Raon-1 mini, HumanEval 164   2878s   75.3 / 110.4    60.2     61.9 °C    65.0 °C
   Raon-1 mini, MMLU-Pro 120    2965s   75.7 / 120.4    62.4     60.2 °C    65.0 °C
   Spark-X2.6, core axes         330s  107.1 / 129.9     9.8     73.0 °C    69.0 °C
   Spark-X2.6, HumanEval 60     2157s   92.1 / 111.6    55.2     67.8 °C    70.0 °C
   Spark-X2.6, 234k needle       515s  101.5 / 125.8    14.5     75.2 °C    77.0 °C
   ─────────────────────────────────────────────────────────────────────────────────
   a full Raon sweep (core + HumanEval + MMLU)  = 139 Wh = 0.139 kWh
   the Spark set measured here                  =  80 Wh = 0.080 kWh
```
Two observations that matter more than the absolute numbers:

- **The short, dense work is the hot part.** The `--core` runs had the highest peak power (118-130
  W) because prefill saturates the GPU for a minute at a time; the long accuracy axes settled at
  75-92 W average, because they alternate generation with Python executing the generated code — the
  GPU idles during test execution. A benchmark's average power is therefore lower than a serving
  workload's. - **Sustained temperature is far below peak.** Over the final five minutes of the long
  runs, Tctl averaged 57 °C (Raon) and 66 °C (Spark), against peaks of 62-70 °C, and the hottest
  single reading in any run was 77 °C on the 234k-token needle. Nothing here is close to a throttle
  point; the box is quiet and cool under sustained local inference, which is the practical case for
  it over a discrete GPU.

### 15.4 What that means in money

At an assumed £0.25/kWh — change the tariff and every figure scales linearly:

```
   one full local sweep (Raon, 139 Wh)        ~3.5p
   one Spark sweep (80 Wh)                    ~2.0p
   keeping the driver resident 24/7 (6 W)     ~£13/year
   ─────────────────────────────────────────────────────────────────
   for comparison, the hosted sweeps in §14:  $0.06 (Haiku) to $0.85 (Sonnet)
```
So the marginal cost of a local sweep is roughly **1/10th to 1/40th of a hosted one**, and the
electricity is not the reason to care: the upfront hardware is. The hosted cost scales with every
future call; the local cost was paid once and then runs at a few pence per sweep.

### 15.5 Which energy mode these numbers were measured in

Every figure above was taken in one specific power configuration, and it belongs with the numbers
the way the kernel and Mesa versions do:

```
   cpufreq driver     amd-pstate-epp   (amd_pstate status: active)
   governor           powersave
   EPP                balance_performance
   platform profile   not exposed — /sys/firmware/acpi/platform_profile is empty on this board
   power daemon       power-profiles-daemon active (its CLI is broken here:
                      powerprofilesctl raises a traceback, so switching is sysfs-only + root)
```
Three things follow from that.

**"powersave" is not a throttle on amd-pstate.** Unlike the old acpi-cpufreq governor of the same
name, it still ramps to full boost on demand; the EPP value only biases how eagerly. The
measurements confirm it: package power reached 130 W and Tctl 75 °C under load, so the box was using
its budget, not idling at a capped clock. Anyone who reads "powersave" and assumes the numbers are
artificially low has it backwards.

**How other modes would move the figures.** These are reasoned expectations from the measured data,
not measurements — they would need a root-level switch and a controlled re-run to confirm:

```
   mode                              package W      tokens/s     temps        Wh per run
   ─────────────────────────────────────────────────────────────────────────────────────
   current (powersave + balance_     as measured    as measured  as measured  as measured
     performance EPP)
   performance EPP / performance     +5-15% peak    +0-10%       +3-6 °C      flat to slightly up
     governor
   power EPP / power-saver           -20-40% peak   -15-30%      -5-10 °C     -5-15%, but more
                                                                               energy per token
```
The pattern to expect is the one this hardware keeps producing: **CPU-side power modes move the
wall-clock and the peak, but barely move energy per token**, because the iGPU is the bottleneck and
the CPU is mostly waiting on it. On a CPU-bound workload the spread between modes would be much
wider.

**Modes change the record, so record the mode.** The history database stores power and temperature
but not the governor or EPP, so a past row cannot be re-attributed to a mode after the fact. Any
future benchmark should write the governor and EPP into its identity row next to the kernel and Mesa
versions — otherwise a row measured in `performance` and a row measured in `power` will look
comparable when they are not.

### 15.6 Caveats

- **These are component figures, not wall-plug figures.** No inline power meter was used, so PSU and
  VRM losses are excluded; a wall measurement would read somewhat higher. - **The two power sensors
  are one domain** on this APU. Summing CPU and GPU columns would roughly double-count. -
  **Benchmark power is not serving power.** Accuracy axes spend time executing generated code, which
  idles the GPU; a chat workload that generates continuously sits closer to the core-run figures. -
  **Three days of database, not three weeks.** Only runs after 2026-10-23 could be profiled; the
  older archive rows in §9 have no power figures and should not be given invented ones.

---

## 16. Uncensored and abliterated models: what the removal actually costs

Three different things get sold as "uncensored", and they behave differently enough that conflating
them ruins the comparison:

```
   ABLITERATED    the refusal direction is found in activation space, then projected out of
                  the weights (orthogonalised). The model keeps its training and loses one
                  direction of behaviour. Small, surgical, and measurable.

   UNCENSORED     a finetune on unfiltered data, or trained with refusal pairs removed.
                  A different model with a different lineage — not the same weights minus
                  a direction.

   MERGE / NSFW   a roleplay or image-oriented merge, often of a different base entirely.
                  Unrelated to either of the above, despite the shared vocabulary.
```
Only the first kind is a controlled experiment. Everything below is about abliteration, and the
document refuses to draw conclusions about the other two from it.

### 16.1 Why removal could cost capability

A refusal direction is not an isolated module. Projecting it out of the weights removes that
direction from *every* weight matrix that happens to have a component along it, so the perturbation
lands in whatever else the model encoded in that direction. In principle the casualties should be
the behaviours that lean on the same structure: instruction-following precision, multi-step
reasoning, and the consistency of long derivations — and code, which is largely pattern-and-syntax,
should be the least affected. The measurements agree with that prediction, on the one pair
available.

### 16.2 The one controlled pair on this box

**Table 10 — gpt-oss 120B base against its abliterated build, same harness and caps.**

| Axis | gpt-oss base | gpt-oss abliterated | delta |
|---|---|---|---|
| HumanEval (164) | 0.9268 (152/164) @cap 1024 | 0.9268 (152/164) @cap 2048 | 0 — identical, with twice the room |
| MMLU-Pro (120) | 0.5833 @cap 512 | 0.7500 @cap 2048 | **not comparable — the cap moved** |
| Riddles + arithmetic (/14) | 12/14 | 10/14 | −2 items |
| IFEval (30, pinned 1280 both) | 0.800 / 0.867 | 0.767 / 0.800 | −1 and −2 items of 30 |
| Decode (tg) | 50.1 t/s | 50.5 t/s | none measurable |
| Refusals on 8 refusal-prone prompts | **0 of 8** | **0 of 8** | none observable |

The two rows carry different caps because the base was measured before the harness forwarded
`--max-gen-toks` to the standalone axes, so its rows record `cap: None` — which means the scripts'
own defaults ran (1024 on HumanEval, 512 on MMLU-Pro), not "no cap". This is the single most common
way these tables mislead, and it decides two of the rows above.

Read it axis by axis:

- **Code: unchanged, to the item — and this is the strong form of "unchanged".** Both scored
  152/164, but the abliterated build had *twice* the generation budget (2048 against 1024) and
  gained nothing. Per §8, a score obtained with more room that comes out equal is clean evidence of
  no regression, because the extra budget was available and unused. Abliteration is not a broad
  capability tax on code. - **Knowledge: not comparable, and the +16.7pp is almost certainly the
  cap.** The base row ran at 512 and the abliterated at 2048. This exact pair has already been
  re-measured at a shared cap elsewhere in this project, and the 0.17 gap resolved to the budget
  rather than the weights. Publishing it as an abliteration effect would be the third time a
  knowledge delta turned out to be a token budget; the honest cell is `not comparable`. -
  **Reasoning traps: −2 of 14.** Both runs used the same 512-token riddle default, so this delta is
  measured under matched conditions, and it is the one quality cost the pair shows. It lands where
  the theory predicts — multi-step constraint-following — and where §10 warns these probes are most
  sensitive. - **Instruction-following: −1 to −2 items of 30.** Both runs went through lm-eval's
  pinned 1280-token budget, so the comparison is matched; at n=30 each item is worth ~3.3pp, so the
  honest label is "possibly slightly worse", not "worse". - **Speed: unchanged.** Same file size
  class, same build, 50.1 against 50.5 t/s.

### 16.3 The behavioural claim did not reproduce — and that is the useful result

Abliteration is bought for one reason: the model stops refusing. On eight prompts chosen to sit near
a safety boundary while having legitimate answers (SQL injection explained for defenders,
bleach-ammonia chemistry, pin-tumbler mechanics, shoplifting fiction, ransomware concepts,
drug-policy argument, gunpowder history, buffer overflows), run at a 1200-token cap:

```
   gpt-oss base          refused 0 of 8
   gpt-oss abliterated   refused 0 of 8
```
The base model of this family does not refuse this class of request in the first place, so the
abliterated build had nothing to remove that these probes could see. Two conclusions, both
practical:

1. **Abliteration is only worth its cost when the base model actually refuses your workload.** Check
   that first with a handful of real prompts. Buying an abliterated build to remove refusals the
   base model never made is paying a capability price for nothing. 2. **"Uncensored" is not a
   quality tier.** Both members of this pair answer the same questions, at the same speed, with the
   same code score. The difference lives in a narrow behavioural band, not in the axes this document
   measures.

### 16.4 The case that must not be attributed to censoring

The other abliterated artifact in the roster is `qwen38fn-abl` (176.9B, IQ3_S): HumanEval 0.8476,
but **MMLU-Pro 0.0083** — one correct answer in 120. That is not abliteration damage; it is a
3.4-bit quantisation of a 177B model, and §5.6 already documents the same collapse in a
non-abliterated file. There is no matched censored comparator at the same quant, so the row says
nothing about abliteration either way.

The same trap catches the boot model. `Ornith-1.5-35B-Uncensored-YMQ-M` (15.1 GiB, IQ3_XXS) was
measured on 2026-10-31 at cap 4096 — **0.5671 code, 0.6333 knowledge, 12/14 riddles** — and at 0.57
it looks like a 26-point ablation bill against the 0.8232 that the standard `Ornith-1.5-35B` build
scores. It is not: that standard row is an `Q4_K_M` file measured at **cap 512**, so the comparison
moves two variables at once (a 3.06 bpw quant against 4.9, and a floor against a real budget) and
the 0.57 figure is the uncensored file *and* its quantisation together. What the run does establish
is that the cap is not the explanation — re-measuring at four times the budget moved one code item —
so the honest label is "an IQ3-class uncensored fine-tune, not a clean abliteration datapoint".

And one file that looks unmeasured is not. `Ornith-1.5-35B-A3B-Abliterated-MTPv2-21G-ICE`
(19.4 GiB, IQ4_XS, with its own MTP drafter) is the file behind the **`ornith-mtp-21g`** rows:
0.9207 code at cap 4096, 0.7750 knowledge at 2048, 11/14 riddles, 65.2 t/s. It is the strongest
abliterated artefact on this box after the uncensored gemma, and it belongs in this section rather
than in the unmeasured list — the alias hid it, not the absence of a run.

### 16.5 How to choose, and what to expect

```
   ┌──────────────────────────────────────────────────────────────────────────────┐
   │ 1. Does the BASE model refuse the prompts you need answered?                  │
   │       no  -> you do not need an abliterated build. Keep the base.             │
   │       yes -> an abliterated build is the right lever; measure these axes:     │
   │              riddles/instruction (likely −1 to −2 items), code (likely nil),   │
   │              and speed (nil)                                                  │
   │                                                                              │
   │ 2. Never compare an abliterated build to a base at a different quant.        │
   │    Quantisation moves knowledge by 2-17pp by itself (§5.3) — it will swamp   │
   │    whatever abliteration did.                                                │
   │                                                                              │
   │ 3. Judge it on the axis you bought it for. If refusals are gone and code and  │
   │    instruction are intact, it did its job — regardless of a knowledge delta   │
   │    that belongs to the quantisation.                                         │
   └──────────────────────────────────────────────────────────────────────────────┘
```
And the caveat that outranks all of them: **abliteration changes what a model will say, not whether
it is right.** A confident wrong answer is still wrong. The one axis where this pair appeared to
improve by double digits did so because the two rows were measured at different token budgets —
which is also the reason this section quotes caps in every cell.

## 17. Why the hosted DeepSeek numbers look the way they do

Two different things decide a hosted score, and conflating them is the most common way to misread
§14: **what the model computes** (architecture) and **how the engine serves it** (systems). DeepSeek
changed both recently, and both are visible in the rows above.

Figure 14 — Where a served number comes from.

```
   ┌──────────────┐   ┌────────────────────────────────┐   ┌──────────────────┐
   │  MODEL       │   │  ENGINE                        │   │  MEASUREMENT     │
   │  architecture│──►│  kernels, batching, caching,   │──►│  ttft, t/s,      │
   │              │   │  speculation, parallelism      │   │  cost per token  │
   └──────────────┘   └────────────────────────────────┘   └──────────────────┘
     fewer bytes        fewer wasted FLOPs, more           quality is the
     per token          tokens per second                  model's; speed is
                                                           the deployment's
```
### 17.1 What changed in the model, in plain terms

Four architectural choices matter for how fast and how cheaply these models run:

- **Sparse attention with an indexer.** Instead of every new token attending to every earlier token,
  a small "indexer" scores the past and only the top few are attended. Cost per token grows much
  more slowly with context than in a conventional transformer. (llama.cpp's own `deepseek4.cpp`
  implements this with an indexer and top-k selection, and ships `llama-kv-cache-dsa.cpp` —
  "DeepSeek Sparse Attention" — so the mechanism is inspectable on this machine.) - **Compressed
  key/value state.** Queries and keys pass through low-rank projections (`q_lora` in the same
  source), so the KV cache per token is far smaller than a same-width dense model's. This is why
  million-token contexts are economic at all. - **Mixture of experts with few active experts.** The
  model holds many parameters and reads only a small fraction per token (`n_expert`). Total size
  sets memory; active size sets speed. - **Multi-token prediction heads** (`nextn`/`mtp`). The model
  proposes several future tokens, which a serving engine can use as drafts for speculative decoding.

The through-line: **these changes reduce both the bytes read and the attention work per generated
token.** That is exactly the quantity that governs performance on a bandwidth-limited machine like
the one this document is about — and exactly what a serving engine can then exploit.

### 17.2 What changed in the engine

DeepSeek open-sourced **DeepInfer** on 2026-10-20, described as the framework behind their
production service, supporting precisely DeepSeek-V4.1-Flash. The features that explain the
measurements here:

```
   kernel suite           FlashMLA, DeepGEMM, DeepEP, DeepSelect, TileKernels — fused attention,
                          matrix-multiply and token-dispatch kernels instead of generic ones
   expert parallelism     experts spread across GPUs, with EPLB rebalancing the hot ones
     + EPLB
   DSpark / NEXTN         speculative decoding using the model's own multi-token-prediction heads;
                          default maximum draft length 5
   SWA bounded replay     do not re-read the whole prompt: replay only a bounded suffix (the V4.1
                          default keeps ~140 tokens) when the model's sliding-window attention
                          makes the rest irrelevant
   async scheduling       overlap the CPU's batch bookkeeping with GPU execution
   deterministic          batch-invariant inference + deterministic sampling: same tokens in,
     sampling             same tokens out, regardless of what else is in the batch
   structured outputs     constrain generation to a regex / JSON schema / grammar

   hardware: NVIDIA SM100 and Huawei Ascend 950 only. Not consumer GPUs, not Vulkan, not this box.
   published benchmarks: 4 SM100 GPUs for prefill, 64 for decode.
```
Note what is *not* in the open release: a KV-cache system, prefill/decode disaggregation, and
cross-replica load balancing. It is a serving stack for a fleet, not a single-machine runtime.

### 17.3 Mapping the engine onto the figures measured here

The measured rows in §14 are consistent with these mechanisms. Read the right-hand column as the
*likely* explanation, not as vendor confirmation — the routes do not publish their configuration.

**Table 11 — Observed hosted behaviour and the mechanism that plausibly produces it.**

| Observation (§14) | Likely mechanism |
|---|---|
| TTFT 1.23s on a 6-8k-token prompt | Bounded SWA replay plus a very high prefill rate: most of the prompt is never re-read |
| 749 t/s decode on the pinned DeepSeek route | Speculative decoding via NEXTN/MTP draft heads, draft length up to 5 |
| 257 t/s decode on the unpinned route, same nominal model | A different serving configuration — the 2.9x gap is the deployment, not the weights |
| 97.7% of prompt tokens cached on one route, 0% on the other | Prefix caching enabled on one route only; the model is identical |
| 5 of 5 identical answers at temperature 0, on every route | Deterministic sampling / batch-invariant inference is now a first-class feature |
| JSON preflight clean on the first attempt, 3/3 | Structured-output support constrains the reply rather than hoping the model complies |
| 24% of output tokens billed as reasoning on the pinned route | The thinking budget is spent inside the same cap, which is why cap-burn counts differ by route |

### 17.4 What this means for the comparison

**The speed gap is a systems gap, not a weights gap.** The local box and the hosted fleet are not
running the same *kind* of thing. Locally you get one model, one GPU, one sequence, no expert
parallelism, no paged KV at fleet scale, no draft tokens in the build used here, and no bounded SWA
replay. The hosted fleet gets fused kernels, dozens of GPUs, speculation and caching. When the same
nominal model served on two hosted routes differed by 2.9x in decode rate, that is the clearest
possible demonstration that these numbers describe deployments.

**The quality gap is a weights gap, and it is the durable one.** HumanEval and MMLU-Pro scores are
properties of the model. They will still be true next month; the t/s figures will not.

**This box could, in principle, run the architecture — it cannot run the weights.** llama.cpp
implements DeepSeek V4 (`deepseek4.cpp`, the DSA KV caches, the indexer), so the *software* is not
the obstacle. The obstacle is arithmetic: the smallest published quantisation of DeepSeek V4.1 Flash
is **120.5 GiB** (measured during the candidate scans, not re-derived here) against a 100 GiB pool.
Even with full kernel support there is nowhere to put it.

### 17.5 The practical takeaway

For a buyer or a newcomer, three sentences:

1. **Do not read a hosted tokens-per-second figure as "this model is fast".** Read it as "this
   deployment is fast", and expect the same weights to be 3-10x slower anywhere else. 2. **Do read a
   hosted accuracy figure as the model's**, because that part travels — subject to the caps and
   reasoning-budget caveats in §7.3 and §14.6. 3. **Architecture improvements make local serving
   cheaper faster than they make it faster.** Sparse attention and compressed KV cut memory per
   token, which is why a million-token context is now ordinary; they do not remove the bandwidth
   ceiling that sets local decode speed.

## 18. For newcomers: what to expect, and what to avoid

The shortest path to a working local model on this hardware, and the mistakes most people make
first.

### 18.1 A minimal path to a working setup

```
   1. OS          Arch/Fedora/Ubuntu, recent kernel. Verify: glxinfo -B shows the Radeon iGPU
   2. Vulkan      vulkaninfo --summary  -> apiVersion 1.4, driverName radv
   3. Build       git clone https://github.com/ggml-org/llama.cpp
                  cmake -B build -DGGML_VULKAN=ON -DCMAKE_BUILD_TYPE=Release \
                        -DVulkan_INCLUDE_DIR=$HOME/.local/include \
                        -DVulkan_LIBRARY=/usr/lib/libvulkan.so
                  cmake --build build -j
   4. Model       one GGUF you can afford: start at Q4_K_M of a 20-30B model (~15-20 GiB)
   5. Serve       ./build/bin/llama-server -m model.gguf -ngl 99 -c 32768 \
                        --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0 --jinja
   6. Test        measure before you trust it: prefill/decode, one JSON probe,
                  one needle, and one arithmetic trap (see section 7)
```
If you would rather not build: Ollama and LM Studio both ship Vulkan-capable llama.cpp builds and
will run most of these models unchanged. What you lose is control over the exact build, the KV-cache
quantisation and the chat template — which, as this document shows, are precisely the variables that
change results.

### 18.2 Pitfalls specific to this platform

1. **Old Mesa is the number one cause of nonsense output.** Below Mesa 25.x on RDNA 3.5 you get
   wrong tokens, not errors. Check `glxinfo -B` before blaming the model. 2. **The first run of a
   new model is not a benchmark.** Vulkan shader compilation makes the first numbers 2-5x too low.
   Warm up once. 3. **GTT is not VRAM.** `mem_info_vram_total` reading 8 GiB is expected; the usable
   pool is `mem_info_gtt_total` (100 GiB). Do not conclude the model will not fit from the VRAM
   number. 4. **Context is a memory purchase.** A 4B model at 1M tokens needed 20 GiB of KV. Decide
   context length before, not after, you run out of pool. 5. **Quantisation is not free at the
   extremes.** 2-bit preserves code and destroys knowledge (0.9451 → 0.3667 MMLU in one measured
   case). 3-bit is usually the practical floor. 6. **Reasoning models need budget or they fail
   silently.** A thinking model with a small cap returns an empty string, which scores zero. Either
   raise the cap or disable thinking. 7. **Chat templates break more models than weights do.** Two
   models here failed all probes for template reasons, not capability reasons. `--jinja` and a
   correct template matter. 8. **Do not run a benchmark alongside anything else.** Shared bandwidth
   means contention halves decode speed; a "slow model" may just have been measured during another
   run. 9. **One session per camera, one model per GPU.** Resource exclusivity is a design
   constraint here, not an inconvenience — it is why `Conflicts=` and the availability guard exist.
   10. **Do not trust a repo name.** A `*-GGUF` repo can contain diffusion weights (one measured
   case declared `arch = wan`). Read the header before a 15 GiB download: `head -c 4M model.gguf`
   and parse the metadata.

### 18.3 What this method cost, and what it bought

**The one cost that is measured:** 118 runs totalling **47.7 hours of benchmark execution**, recorded
run by run in `catalogue.json`, over 2026-10-07 → 2026-10-31. Of the 33 model files measured, 16 remain
servable and 24 retirements are recorded in the ledger; the two largest deletion passes alone released
61.6 GiB and 245.1 GiB.

A full sweep on a 120B model takes 2-4 hours of that budget, and the HumanEval axis is the expensive
one at 20 minutes to 2 hours depending on the model. The benefit is that every decision is a line in
the catalogue rather than an opinion, and a re-test — of a new quantisation, a new llama.cpp build, or
a model released next week — is a command rather than a project.


### 18.4 Effort: what it took, and what it would take you

Every other number in this report traces to a run. This one does not, and is labelled accordingly:
it is a **reconstruction from artefacts** — line counts, run wall times, document revisions — not a
time log. Ranges, not a point estimate.

| phase | low (h) | high (h) | what drives it |
|---|---:|---:|---|
| planning and design | 15 | 25 | seven axes, the cap policy, the memory and quantisation model (§5) |
| harness and tooling | 70 | 100 | ~4,500 lines: bench harness, chart renderer, 19 run scripts, publish pipeline |
| running and supervising | 45 | 60 | 47.7 h of measured execution, ~18 h of per-model setup, re-runs and failed loads |
| analysis and correlation | 30 | 45 | alias-collision audits, cap-floor re-measurements, four external sources compared |
| writing and revision | 50 | 70 | 2,655 lines across six editions, the ledger, ten captioned figures |
| publishing | 12 | 18 | repository, sanitising gates, Pages, discovery metadata, the two probes |
| **total** | **222** | **318** | ≈ 250-300 h |

Of that, roughly **40-60 hours needed a person**: the decisions the measurements cannot make — what to
delete, what to publish, whether 0.57 is a fact about the model or a bug in the harness. The remainder
is machine execution and agent time, which is why the per-byte cost of this hardware is not the scarce
input; the discipline around it is.

**Reproducing it elsewhere is far cheaper than making it once.** The harness, the pipeline and this
document's structure are public (`tools/` in the repository), so reproducing the numbers on another
board is roughly **40-60 hours**, mostly bench wall time and per-model setup. One caveat that matters:
capability rows should reproduce within a couple of percentage points, but decode will not — a
different kernel, Mesa version or llama.cpp build moves throughput 10-20 %, which is exactly why every
row here carries a build column.

---

## 19. The same data, plotted

Ten figures, generated from the archive rather than drawn by hand: `~/docs/charts.py` reads
`~/runs/catalogue.json`, `~/bench/api-calls.jsonl` and the hardware monitor's database, and writes
SVG that is embedded in this page. Nothing in them is typed in, so a figure cannot drift away from
the tables the way a copied number can.

Three rules govern what appears. The rows §8 warns about are removed before plotting — the
placeholder carrying exactly 1.0 at `cap: None`, and the extractor failure with a near-zero MMLU
(`qwen38fn-abl`'s 1/120). Each model contributes its **best** measurement per axis, the same rule
Table 4 states, and aliases are funnelled through one canonical name per weight file first, because
the run alias is not unique: `gemma4-26b-a4b` was used for both the Q8_0 and the QAT Q4_0 file,
`ornith35b` for both the uncensored boot file and the text-only Q4_K_M, and the Bolt file appears
under three names. Before that fix, two figures compared a file with itself. And any point whose cap
or item count would change how it should be read is marked on the figure itself, because a clean
chart that quietly compares a 512-token run with an 8192-token one is worse than no chart at all.

The figures are **all-time**: 55 model files, 27 with a HumanEval row, 27 with MMLU-Pro, 20 with
everything. Ten of those files have since been retired, and they are still plotted — a plotted point
is a measurement, not a recommendation, and the roster view is Table 4b.

Rebuild with `~/docs/.venv/bin/python ~/docs/charts.py`; each figure is a standalone SVG in
`~/docs/charts/`, inked with the page's own CSS variables so it follows the light and dark themes.

### 19.1 Code quality against decode speed

The trade this box actually forces. The live roster occupies the 0.95-0.96 band at 57-65 t/s
(gemma4-26b-uncen, minicpm-v47-35b) and at 23 t/s (ornith-122b); the best all-time points are the
retired 31B at 0.9634 and 17 t/s and the retired Q8_0 at 0.9573 with 49.4 t/s. Every point at or above
0.9512 spans 17 to 65 t/s — a 3.8x spread — so quality does not set speed on this box: bytes read per
token do, which is why the 25-35B MoE cluster outruns the dense files at the same score. The corner
that is genuinely empty is "best code *and* best speed"; nothing has both. Bubble area is parameter
count; hollow markers are floor estimates from a small cap or a short subset.

*Does not show* long-prompt behaviour — that is prefill, and §13.2 is where it matters.

{{svg charts/f15-quality-speed.svg}}

Figure 15 — HumanEval pass@1 against decode throughput, 27 models.

### 19.2 Knowledge against decode speed

The same axes with the other quality measure, and a different ranking. Speed buys no knowledge: the
two fastest files (mellum21 at 111.9 t/s, lfm25 at 106.6) read 0.8083 and 0.6917, and the best
knowledge-per-second point on the box is mellum21, still 5.8pp under the ceiling. That ceiling belongs
to two retired files — the 31B and the Q8_0, both 0.8667 — with the live driver at 0.8500. The 2-bit Bolt load (0.3667) sits visibly detached from the rest of the nemotron family.

*Does not show* the hosted tier, which is deliberately absent (§19.8).

{{svg charts/f16-knowledge-speed.svg}}

Figure 16 — MMLU-Pro against decode throughput, 27 models.

### 19.3 The cap is a variable, not a detail

Six models in the archive were measured at two generation budgets, each pair joined by a line.
nemotron-super-120b moves 0.835 → 0.951 HumanEval between a 2048 and a 4096 cap; lfm25 0.445 → 0.854;
mellum 0.177 → 0.878 between a 1024 and a 4096 cap, which is the largest single move in the figure
and is a budget artefact, not a model result. Against that, qwen3next-q6 gets *slightly worse* with
more room (0.9296 → 0.9207), because it was never budget-limited. Grey dots are models measured once,
shown for context only.

*Does not show* the worst case, sage-a1.5 with thinking on, where all 20 items burned the cap and
returned nothing — that run has no score to plot (§7.3).

{{svg charts/f17-cap-sensitivity.svg}}

Figure 17 — HumanEval against generation cap for the six models measured twice at n ≥ 100.

### 19.4 The league tables, as bars

The four capability axes at once, top fifteen per axis, with the cap printed only where it differs
from the 2048 default. Sorting each axis separately is the point: no model tops two of them, and the
retired files are still in the bars where they led — which is exactly how a reader can see what a
deletion cost.

{{svg charts/f18-leader-bars.svg}}

Figure 18 — Per-axis leaders: HumanEval, MMLU-Pro, IFEval and riddles.

### 19.5 What quantisation changed inside four pairs

The four controlled pairs of §5.3 as deltas rather than claims, arithmetically: hy-memory Q4_K_M →
Q8_0 is −1.2 pp code, +2.5 pp knowledge, −22.3 t/s; mellum Q6_K → Q4_K_M fork is +3.7 pp code,
+10.8 pp knowledge, +17.8 t/s; **gemma4-26b Q8_0 → QAT Q4_0 is −0.6 pp code, −2.5 pp knowledge,
+10.1 t/s for 11.6 GiB less**; gpt-oss base → abliterated is 0.0 pp code and a hatched +16.7 pp
knowledge. Two of the four aggressive directions win on at least one axis. The hatched bar is the one
comparison the archive cannot support — gpt-oss knowledge at 512 against 2048 — drawn hatched,
starred and greyed rather than dropped: omitting it would hide the confound, drawing it plainly
would launder it.

{{svg charts/f19-quant-pairs.svg}}

Figure 19 — Within-pair change: second variant minus first.

### 19.6 Where a family is actually consistent

Min-max spread per family, each member at its own quantisation and cap. gemma4 is tight on both axes
(Δ 0.022 code, Δ 0.025 knowledge across four files); nemotron spans 0.773 on code because a broken
2-bit load sits inside the family; qwen3.6/3.8 spans 0.058 on knowledge once the poisoned 1/120 cell
is filtered — which is the single respect in which this figure and §10.2's table disagree, and the
figure is the one following §8's rule. `other` is the catch-all family and is wide by construction,
not by lineage.

{{svg charts/f20-family-spread.svg}}

Figure 20 — Within-family spread on the two ranked axes.

### 19.7 One profile per model

Specialists and the generalist on one scale: the eight highest-scoring of the twenty models with
every axis measured. The gemma4 lines are flat and high across all six axes; ornith-122b trades
speed for code; mellum peaks on throughput and sags on knowledge; nemotron-super is knowledge-heavy
and slow. Three of the eight are retired (the 31B, the Q8_0, and Mellum's Q6_K), so the flat-and-high
shape you see is partly a picture of what is no longer on disk. Each axis is normalised within the
plotted set, so the figure is about shape, not absolute quality.

{{svg charts/f21-profiles.svg}}

Figure 21 — Six-axis profile of the eight best-scoring models with every axis measured (of 20).

### 19.8 Hosted routes, measured

What each hosted route's money buys, across the five routes measured: the pinned DeepSeek route has
the lowest time-to-first-token and the highest effective throughput, Sonnet the highest cost per call
by an order of magnitude. The local driver is marked for scale.

*Does not show* hosted accuracy, and that gap is worth naming: the HE and MMLU rows in §14 were
logged in that session, not written to a run file, so they cannot be plotted without breaking the
rule that every figure comes from the archive. Re-running `~/bench/bench-api-model.sh` for the five
routes (about $1.25 at the §14.4 rates) would close it.

{{svg charts/f22-hosted-routes.svg}}

Figure 22 — Hosted routes: latency, effective throughput and cost per call.

### 19.9 Power through one run

Package power at 1 Hz through the full suite run on the live driver
(`20261028-123736-gemma4-26b-uncen-full`, 2,078 samples over ~39 minutes): **mean 78 W, peak 123 W**,
idle floor 6 W. The spikes are prefill bursts; the troughs are Python executing generated code, which
is exactly why a benchmark's average power understates a serving workload's (§15.3).

This trace used to be the 2026-10-27 flint40b-abl run, whose model has since been retired and whose
1-second samples have rolled up out of the raw window — the figure could no longer be rebuilt, so it
now points at a run that can be. Mean and peak rose from 69/123 W to 78/123 W with the new target:
same box, longer run, more prefill.

{{svg charts/f23-power-run.svg}}

Figure 23 — CPU package power through the 2026-10-28 full suite on gemma4-26b-uncen.

### 19.10 What abliteration cost

The one controlled pair on five axes at true scale. Code and speed are identical (0.9268 both,
+0.9 t/s); riddles and instruction-following each lose one to two items; knowledge is hatched
because the two rows ran at different caps and the +16.7 pp is the budget, not the weights (§16.2).

{{svg charts/f24-abliterated-pair.svg}}

Figure 24 — gpt-oss 120B base against its abliterated build.

---

## 20. Appendix

Reference material: the commands used, the port map, where everything lives, and a glossary of
terms.

### 20.1 Commands

```bash
# serve a model (swaps out whatever is resident)
~/llama-local/llama-switch gemma4-26b-a4b

# quick core sweep: perf, preflight, needles, riddles  (~10 min)
~/bench/bin/t20 --port 8099 --core --max-gen-toks 4096 --tag quick

# full sweep: + HumanEval 164, MMLU-Pro 120, IFEval 30
~/bench/bin/t20 --port 8099 --max-gen-toks 4096 --budget 3600 --tag full

# individual axes
~/bench/.venv/bin/python ~/bench/humaneval.py --port 8099 --limit 164 --max-tokens 4096
~/bench/.venv/bin/python ~/bench/mmlu_pro.py --port 8099 --limit 120 --max-tokens 4096

# benchmark without disturbing the resident model
systemd-run --user --collect --unit=bench-x --property=Type=simple \
    bash ~/llama-local/run-<model>.sh

# long-context retrieval probe (port, target tokens)
~/llama-local/needle-long.py 8180 200000

# hosted model through the shim, then the same axes as any local unit
~/.hermes/.env && set -a && . ~/.hermes/.env && set +a
~/bench/api-shim.py --model anthropic/claude-sonnet-5.5 --port 8300
~/bench/bin/t20 --port 8300 --core --max-gen-toks 4096 --tag sonnet
~/bench/bench-api-model.sh anthropic/claude-sonnet-5.5 8300 sonnet full   # core + HE + MMLU
/usr/bin/python3 ~/bench/cache-probe.py --prefix-tokens 6000 --repeats 4

# build identity of whatever is serving right now (§4.1)
curl -s localhost:8099/props | jq -r .build_info          # -> b3-1a33095
~/llama-local/halo-box-strix-llama.cpp/build/bin/llama-server --version

# re-stamp build identity on legacy catalogue rows (prints first, writes only with --apply)
~/bench/annotate-builds.py
~/bench/annotate-builds.py --apply
```
### 20.2 Ports

```
   8082 qwen3next        8083 qwen3next-q6     8084 ornith-122b
   8085 gptoss           8086 ornith            8093 qwen38-35b
   8096 gptoss-abliterated 8097 qwen38fn-abl    8098 ornith35b (user unit)
   8099 gemma4-26b-a4b    (script only, unit disabled)
   8100 gemma4-26b-uncen  (ENABLED — the WhatsApp channel driver)
   8181 lfm25-24b-a2b    8185 ornith-mtp-21g    8186 minicpm-v47-35b
   8189 nemotron-super   8094 orient-ornith (SYSTEM unit, boot model)
   8090 the hardware monitor (hardware monitor, private network only)   8188 ComfyUI (image generation)

   Retired 2026-10-29/30 and no longer bound: 8087 kimi, 8091 mellum, 8095 qwen38-27b,
   8180 nemotron-bolt, 8182 hy-memory, 8184 ling3-flash, 8185 gemma4-31b, 8187 nemotron-bolt-e4b
```
### 20.3 File map

```
   ~/bench/                     harness: t20.py, checks.py, humaneval.py, mmlu_pro.py, benchlib.py
   ~/bench/annotate-builds.py   backfills build tree/commit onto legacy catalogue rows (dry-run)
   ~/bench/api-shim.py          exposes a hosted model as a llama.cpp-shaped /v1 endpoint
   ~/bench/bench-api-model.sh   full sweep against a hosted model (core + HE + MMLU) with cost log
   ~/bench/cache-probe.py       prompt-cache hit rate, cost and TTFT per hosted route
   ~/bench/hosted-extras.py     determinism, streaming latency and reasoning-token share
   ~/bench/api-calls.jsonl      per-call tokens, cached tokens, reasoning tokens, cost
   ~/runs/catalogue.json        one row per axis per model — source of every table here
   ~/runs/*.jsonl               per-item results, one file per axis per run
   ~/llama-local/llama-switch   24-unit switcher; writes .intent-model
   ~/llama-local/model-guard.sh availability guard (60 s timer, 3 restarts/hour budget)
   ~/llama-local/run-*.sh       one launch script per model (flags live here)
   ~/llama-local/WIRING-*.md    wiring log and per-model verdicts
   ~/llama-local/RETIRED-models.md  recipes for every model deleted after measurement
   ~/.config/systemd/user/llama-*.service   24 units, mutually Conflicts=
```
### 20.4 Glossary

**Table 12 — Glossary.**

| Term | Meaning |
|---|---|
| **prefill (pp)** | tokens/second while reading the prompt; governed by compute |
| **decode (tg)** | tokens/second while generating; governed by memory bandwidth |
| **ttft** | time to first token — for long prompts this is almost entirely prefill |
| **GTT** | Graphics Translation Table: the GPU-addressable window into system RAM |
| **MoE** | Mixture of Experts: many parameters, only a few active per token — fast but large |
| **active parameters** | the subset read per token; the number that sets decode speed |
| **quantisation** | storing weights in fewer bits (Q4 = ~4 bits); trades fidelity for speed and size |
| **bpw** | bits per weight — the actual density of a quantisation |
| **KV cache** | per-conversation attention memory; grows linearly with context length |
| **cap** | maximum tokens a model may generate per test item |
| **cap-burn** | an item that produced nothing because it exhausted the cap |
| **preflight** | the three-probe gate: non-empty, valid JSON, one-word answer |
| **needle** | a planted fact that must be retrieved from the middle of a long context |
| **IFEval** | instruction-following benchmark with verifiable constraints |
| **HumanEval** | code benchmark scored by executing unit tests against generated functions |
| **MMLU-Pro** | four-option knowledge benchmark |
| **PPL / temp / top-p** | sampling controls; all measurements here use temp 0 for determinism |

---

## 21. Change log

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
- **Still a floor:** `qwen38-35b` and `Ornith-1.5-35B` (the Q4_K_M file) remain cap-512 rows.
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

The models directory is 602 GiB and holds 16 artefacts, every one with a capability row — the last
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
so it could no longer be rebuilt; it now plots the 2026-10-28 full suite on the live driver
(2,078 samples, mean 78 W, peak 123 W).

**Known open items.** `qwen38fn-abl`'s
MMLU-Pro cell is a poisoned 1/120 rather than a score; `qwen38-35b` and `Ornith-1.5-35B` were both
measured only at cap 512, so their code rows are floors, not ceilings; and the driver's context curve (§23.2) now covers 32k, 64k and 113k prompts — but no *other* model
on disk has been measured beyond an 8k needle since the kernel moved to 7.3.0-5.

---

## 22. Credits and tooling

**Measurement.** Every figure here was produced by `~/bench/t20` and the per-axis scripts on the
machine described in §2, run by the operator between 2026-10-07 and 2026-10-31. The numbers come from
those runs and from the hardware monitor's SQLite history; none is estimated, and each is traceable to
a run id in `~/runs/catalogue.json`.

**Assistance.** The benchmark runs, the analysis and the drafting of this document were carried out
with **Hermes Agent (Nous Research) driven by DeepSeek's `deepseek-flash`** model, working alongside the
operator: the agent scheduled and monitored the runs, read their outputs, built the tables and figures,
and maintained the retirement record. The model did not produce any measurement — it read them.

**Publication.** The public site is generated from these same sources by `scripts/build.sh`, which
refuses to publish if a sanitising check fails, and the retirement ledger is published beside this
report. Corrections are welcome as issues on the repository.

---

## 23. Prior art — what exists already, and which question each source answers

This is not the first measurement set for this hardware, and pretending otherwise would be the
fastest way to be dismissed. Four public sources cover overlapping ground; none of them covers the
capability axis at a usable sample size, which is the gap this report exists to fill.

| Source | Hardware / stack | Answers | Does not |
|---|---|---|---|
| [`lhl/strix-halo-testing`](https://github.com/lhl/strix-halo-testing/tree/main/llm-bench) | pre-production Framework Desktop, Arch, ROCm 7.0 nightlies, llama.cpp b5863 (Aug 2025) | `llama-bench` p/n sweeps 128→8192 across flash-attn on/off and Vulkan vs ROCm, plus the tuning that actually moves this box: `amd_iommu=off`, a GTT `modprobe` fragment, `tuned accelerator-performance`, ~215 GB/s of the 256 GB/s theoretical | any capability axis; models from 2025 that are no longer on this roster |
| [`kyuz0` toolboxes](https://kyuz0.github.io/amd-strix-halo-toolboxes/) | containerised backends | pp512/tg128 per backend, kept currentish, so it answers "which runtime" rather than "which model" | capability, caps, per-quant attribution |
| [`pepuscz/strix-halo-llm`](https://github.com/pepuscz/strix-halo-llm) | BOSGAME M5, Ubuntu 26.04, kernels 7.0.0-29/31, ROCm and Vulkan arms | context scaling from 2K to **491K** with cold five-needle retrieval and a `prompt_sha256` per point; a 30-item quality suite (10 coding / 10 GSM8K / 10 math, thinking off, caps 512/1024/2048, published fixture hashes) over four Flash-class models | sample size (30 items ⇒ 3.3 pp per item); quant lines that are deployable at 128 GB; anything under 24B |
| [`llamaperf.com`](https://llamaperf.com/gpu/strix-halo-128gb) | community, mixed setups | 323 reported throughput figures for "Strix Halo 128GB", sortable by context and quant, plus a fit calculator | normalisation — context, quant and offloading differ per report, so two rows are rarely comparable |
| **this report** | CachyOS, kernel 7.3.0-5, Mesa/RADV, llama.cpp fork `1a33095` | capability at n=164 and n=120 **with the cap stated**, per-file quant attribution, build identity per run, and a ledger of every model retired and why | long-context behaviour (until §23.1), prompt-level hashes, and anything that does not fit in 100 GiB beside a resident driver |

### 23.1 Where the datasets overlap, and where they disagree

Exactly one model is measured on this GPU by both this report and `pepuscz/strix-halo-llm`:
Qwen3.8-Flash-Next. Theirs, at Q4_XL on Ubuntu's Vulkan stack: **465 t/s prefill, 42.8 t/s decode**
at a 1.9k prompt. Ours, `qwen38fn-abl` at IQ3_S on CachyOS/RADV: **448 t/s prefill, 52.9 t/s decode**.
Different quant (smaller here, hence faster decode), different kernel and driver — the two are
consistent rather than contradictory, which is the useful outcome: two independent stacks landing
within 10 % of each other on prefill is evidence the harness is measuring the machine and not itself.

Their quality suite and this one are not comparable either, and the arithmetic says why: 30 items
means one task is 3.3 pp, so "30/30" versus "29/30" is a single question. That is not a criticism of
their suite — it is the right size for "did this deployment break the model" — but it cannot rank
models, which is what 164 HumanEval items with executed tests and 120 MMLU-Pro items can do.

What this report borrowed after reading theirs: the prefill/decode split recorded per point rather
than per run (§23.2), and the practice of hashing the prompt. What it did not borrow: their hardware
assumptions, which are Ubuntu's ROCm/Vulkan stack on a different kernel — every throughput figure
here would need re-measuring to be quoted against theirs.

### 23.2 Context scaling of the deployed driver

The open-items list has said since the kernel moved to 7.3.0-5 that no 32k needle had been run. It
has now, on the model that actually answers this machine's traffic, with no model load and no unit
change — `checks.needle` at five depths, recording the prompt length the server reported and its own
prefill/decode rates. Run `20261031-ctxcurve-driver`, rows in `~/runs/ctxcurve-driver-20261031.jsonl`.

| prompt tokens (server-reported) | needle retrieved | prefill t/s | decode t/s |
|---|---|---|---|
| 1,809 | PASS | 1715 | 57.2 |
| 7,098 | PASS | 1671 | 57.7 |
| 28,251 | PASS | 1342 | 50.2 |
| 57,810 | PASS | 1006 | 46.4 |
| 112,862 | PASS | 670 | 37.7 |

Five depths, one run each, no retries needed. Retrieval **held at every depth**, including a 112,862-token
prompt — the answer came back correct with the needle planted in the middle of the haystack.

What degrades is throughput, and the two curves are not the same shape. Prefill falls **2.6×** from
1,715 t/s at 1.8k to 670 t/s at 113k, because attention cost grows with context. Decode falls **1.5×**,
from 57.2 to 37.7 t/s. For chat the decode number is the one that matters: a conversation that reaches
113k tokens answers about a third slower than one at 2k, and the cliff between 58k and 113k is steeper
than the one before it. The practical reading is to compact well before 64k rather than at the edge of
the window — the model is not forgetting anything, it is just getting slow.

Configuration: the deployed driver (`gemma4-26b-uncen`, QAT uncensored Q4_K_M, ctx 131072) on the
Vulkan/RADV stack, measured against the live unit with no reload. This is the behaviour of the model
that answers this machine's traffic, not of the best model on the box — §9.1 explains why those differ.

### 23.3 Cross-validation on their suite — and what their harness had to fix

The strongest check available was to run *their* 30-item suite on *our* deployed driver, unchanged: same
prompts, same per-item caps (512 / 1024 / 2048), temperature 0, coding answers executed against the
fixture's own `gold_test`. Fixtures pinned at `Luce-Org/lucebox@90f85fa`, which is the commit their
results cite.

**Result: 30/30** — coding 10/10, GSM8K 10/10, math 10/10. The same score their Qwen3.8-Flash-Next
deployment reported, from a different model on different hardware. Two independently built harnesses,
same verdict: the suite is not measuring itself.

**But the first pass scored 26/30, and every one of the four misses was the harness, not the model.**
That is worth recording, because it is the failure mode this report keeps warning about in its own
axes:

| item | first-pass verdict | what actually happened |
|---|---|---|
| `gsm_06` | FAIL, "got 16" | answered **$64** correctly; the grader took the last number in the sentence — "for the 16 glasses" — as the result |
| `gsm_08` | FAIL, "got 40" | answered **160 minutes** correctly; same bug, via "(or 2 hours and 40 minutes)" |
| `math_04` | FAIL, "got -2/3" | answered **−2/3**, which is the gold `-\frac{2}{3}`; the grader compared LaTeX to plain notation without normalising |
| `math_08` | FAIL, "got \frac{20" | answered **20/3**, which is *correct*; the fixture's `gold_answer` says 20 and the source's own results.json records "math_08 reference corrected to 20/3". A naive `\boxed{…}` regex also truncated the nested braces |

Three grader defects and one fixture error, all on answers the model got right. Fixing them — answer-marker
parsing, LaTeX-to-fraction normalisation, balanced-brace `\boxed{}` extraction, and the documented
`math_08` correction — gives the 30/30 above, and the run is auditable: `~/runs/lucebox30-driver-final.jsonl`
records, per item, the numbers found in the answer sentence and the raw final text.

The lesson generalises, and it cuts at this report too: **a score is only as good as the grader, and the
grader is usually not published.** Their suite publishes its fixtures and hashes, which is why the four
errors could be diagnosed rather than argued about. Any quality number quoted without its harness and
its normalisation rules carries an unknown error bar — on 30 items, 4 items is 13 pp.

---

*Version 1.9.1 · measurements 2026-10-07 → 2026-10-31; build register (§4.1)
and plotted figures (§19) added 2026-10-27; roster and row corrections 2026-10-30; the Qwen3-Next Q4
capability row 2026-10-31 (§21). Numbers are
reproducible from `~/runs/catalogue.json`; per-model recipes for anything deleted live in
`~/llama-local/RETIRED-models.md`.*

---

*Source, data and build scripts: [github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io](https://github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io). Every row above is backed by a run id in [`data/catalogue.json`](data/catalogue.json); corrections are welcome as issues there.*
