# Testing Local LLMs on AMD Strix Halo
> **Also published:** [Leaderboards by axis](leaderboards.html) — code, knowledge, reasoning, decode and prefill, each row with its cap and build · [Retired models — what was deleted, why, with hashes and restore recipes](retired-models.html) · [Change log](changelog.html) — every correction and the numbers that forced it · [16 GiB of VRAM — local LLMs](16gb.html) — what fits on a 16 GiB card, what it scores, and why the answer changes with the memory architecture.


**Why this rig exists, how it is measured, what the numbers mean, and which model to pick for what**

- **Host:** Minisforum **MS-S1 MAX** (product_family `MINISFORUM`, board `SHWSA`, BIOS 1.06, EC 0.15)
  · OS: CachyOS Linux · GPU: Radeon 8060S (Strix Halo, gfx1151)
- **Runtime:** llama.cpp on Vulkan · **Harness:** `~/bench` (`t20`)
- **Archive:** `~/runs/catalogue.json` · **Measurements:** 2026-10-07 → 2026-11-08
- **Roster:** 16 servable model families on disk, 709 GiB, checked 2026-11-08 · **Change log:** §21

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
  13   Strix Halo vs Nvidia vs Apple    three memory models, bandwidth, ecosystem, who should buy what
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

### 0.0 In plain terms

This is a test of **30 AI models on one small computer** — a Mini-PC the size of a hardback book, with a
single AMD chip and 128 GB of shared memory. Everything here runs on that machine, offline, with no cloud
account. The question was simple: which of these models is worth using, and what does each one cost you in
speed?

**Five things came out of it.**

1. **The best model on this machine is a small one.** A 26-billion-parameter model in 15.6 GB is the best
   all-round model I tested — first on knowledge among everything on disk, joint-first on code — and it is what
   answers my messages. The 35B and 120B files beside it beat it on neither axis.

2. **Bigger is not better, because speed comes from how much of a model runs per word.** Most modern models are
   *mixtures*: for each word they activate only a few of their many parts. A 120B model that wakes 5B parts per
   word can be faster than a dense 31B that wakes all of them — and on this machine that is the whole game,
   because the limit is how fast memory can feed the chip, not how much fits in it. The 120B-class models here
   are 2-2.5× slower than the 26B and score lower on both tests. They earn their 60 GB back for nothing
   measurable.

3. **Coding ability and knowledge are different skills, and a model can have one without the other.** One 35B
   model I tested writes good code (0.8598) and knows almost nothing (0.3250) — it answers a multiple-choice
   question with a guess in a fifth of a second. Another is the reverse. A single "quality" score hides this, so
   every model here is scored on both, plus a set of riddles that catches models which answer confidently and
   wrongly.

4. **Squeezing a model smaller costs knowledge before it costs skill.** Compressed to 2 bits per weight, a model
   still writes code at 0.9451 but drops to 0.3667 on knowledge — the facts go first. On the other end, an 8-bit
   version of a model was no better than its 4-bit sibling and ran 8 tokens/second slower, for 10.5 GB more
   disk. Four bits is the sweet spot here.

5. **Uncensoring is usually free — but only when it is done properly.** Where a well-made uncensored build
   existed, it scored within a couple of points of the original. Where a model looked badly damaged after
   uncensoring, the real cause turned out to be aggressive compression, not the uncensoring at all.

**What it costs to run.** A full test sweep draws about 0.14 kWh — roughly 3.5 pence. The machine idles at
6 watts, about £13 a year. The expensive part is the time, not the electricity.

**What to use, in one line each.** Chat and general work: the 26B driver on port 8100. Bulk classification or
summarising: a 12B model at 111 tokens/second. A million-token document: Kimi-Linear. Images: MiniCPM-V. Every
one of those is on disk and measured; anything that lost its slot has been deleted, and the ledger says why.

**What this cannot tell you.** Each score is 164 code problems and 120 knowledge questions, so a gap under about
5 points is noise, not a finding. One machine, one version of the software, one set of settings — another box,
another build or another kernel will move speed by 10-20% while the quality scores hold. Everything below is
written to make those limits visible rather than to hide them behind a single number.

### 0.1 The technical framing

Seven claims carry the rest of the document.

1. **Leaderboards do not answer the question.** A published benchmark score tells you how a model behaves on
   someone else's hardware, at someone else's prompt length, with someone else's sampler. On a
   bandwidth-limited integrated GPU, a model that is excellent in theory can be unusable in practice — too
   slow, too large, or quietly broken by a chat template. The only score that matters is the one this machine
   produces at the caps this machine will actually serve.

2. **The binding constraint is memory bandwidth, not capacity.** With 128 GB unified and a 100 GiB
   GPU-addressable pool, almost nothing this machine can run is too big. What separates models is how many
   bytes each generated token must read: a 26B model with 4B active parameters runs ~3x faster than a 31B dense
   model of similar size. Choosing a model here is mostly choosing an active-parameter count.

3. **A cheap gate catches most bad candidates.** Three probes — non-empty reply, valid JSON, one-word answer —
   cost under a second and rejected models that scored well on published code benchmarks. Run the gate first;
   do not spend an hour on HumanEval to discover the model repeats itself.

4. **Cap-burn is not the same as being wrong.** These models are scored at a fixed generation cap. A reasoning
   model that thinks past that cap returns nothing and is marked failed. Reading a score without reading the cap
   and the burn count is how good models get discarded and bad ones kept.

5. **Quantisation on this machine is a performance decision before it is a capacity decision.** Decode is
   bandwidth-bound, so fewer bits per weight means more tokens per second — measured at +22% and +43% in two
   pairs. The conventional "quantise only to fit" framing is a CUDA habit and gives the wrong answer here.

6. **Results do not transfer across a family in the way intuition suggests.** Code scores travel within
   ±2-3pp across a family at fixed quantisation; knowledge moved by 16.7pp and 50pp inside two families here,
   and speed does not transfer at all. §10 sets out exactly what may be inferred.

7. **The frontier's lead is axis-specific, and smaller than expected.** Measured with this harness, the best
   hosted model is 1.2pp ahead of the best local model on code — inside the noise — but 5.8pp ahead on
   knowledge, and the cheap hosted tier scores *below* a local 30B on knowledge. §14 has the numbers, the cache
   economics and the confounds.

### 0.2 Conventions used throughout

**`MMLU` in a compact score or table cell means MMLU-Pro** (the 120-item chat 0-shot probe described in §6.2),
never the original 14,000-item MMLU; the full name is written out wherever the distinction matters. **GTT** is
the Graphics Translation Table — the GPU-addressable window into system RAM, which on this machine is the
100 GiB pool that actually matters (§2.1), not the 8 GiB reported as VRAM. **SE** is the standard error of a
proportion, quoted whenever two scores are close enough that sampling noise could explain the gap; at n=164
that is ±2.3 pp at p=0.9, at n=120 it is ±2.7 pp (§8 has the full table).

### 0.3 What exists as a result

A roster of **15 servable models** with measured profiles; a deployed daily driver — the uncensored QAT Q4_K_M
build of gemma4-26b-a4b on port 8100, which since 2026-10-28 is what answers WhatsApp, with
Ornith-1.5-35B-Uncensored on :8094 as the system boot model; a documented set of models that were measured,
failed or lost their slot and were deleted, with hashes and restore recipes; and a measured comparison against
hosted frontier models that establishes how large the gap actually is. Port 8099 (the QAT Q4_0 driver named in
earlier editions) still has its script but its unit is disabled; only one model unit is enabled at a time and
:8100 holds that slot.

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

### 2.3 Storage and paging — what the drives do and do not affect

Worth one paragraph because it is the component most often over-attributed in local-LLM write-ups.

```
   system + models   BIWIN X570 PRO 4 TB NVMe      ~600 GiB of GGUF live here; the root and /home
                                                   filesystems share one btrfs partition
   spare             Netac 2 TB NVMe               unmounted, no filesystem in use
   swap              /dev/zram0, 117 GiB           compressed RAM (priority 100), vm.swappiness 150
```

**Storage affects load time and nothing else measured in this report.** Decode is bound by LPDDR5X
bandwidth (~256 GB/s shared with the CPU) and prefill by shader occupancy; neither reads the SSD once
the weights are resident. A model loads from NVMe at the drive's sequential rate — a 42.9 GiB file
appears in a few tens of seconds — and is then faulted into GTT and never re-read.

**Paging is deliberately not disk-backed.** Swap is a zram device, so any pressure costs CPU to
compress and decompress rather than NVMe reads. That distinction matters when reading a benchmark:
a model whose weights were paged out still pays a fault-in on its next request, but it pays it in
cycles, not in I/O. Every run recorded here was taken with the server's weights resident, and §5
explains how the pool is sized to keep them that way.

### 2.4 What is unusual, and what that costs

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
   halo-box-strix (fork)       1a3309516   0.5.0-dev (b3, commit 1a33095)      0.25.3  10-16 → 11-08
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

### 4.2 What a rebuild would buy — measured, 2026-11-01

The fork's own `origin/HEAD` was **1,041 commits ahead** of the build every row in this report was measured
on, and its delta contained exactly the two changes that could plausibly move numbers here: a Vulkan
**MoE gate+up+SwiGLU fusion in one weight-streaming MUL_MAT_ID launch** (#223, q4_K/q5_K/f16/f32 chains) and
a fix that **stops chunking q8_0/q6_K mat-vec batches of up to 8 columns** (#241) — the cache type most
recipes here use. So it was built and A/B'd rather than taken on faith: scratch worktree at `f5c0a7a34`
(server `0.6.0-dev build 12294`, libggml ABI **0.26.0**), same weights, same flags, same day, only the
binary differing.

| arm | model | decode (reps) | prefill (reps) | quality |
|---|---|---|---|---|
| `1a33095` (served) | gemma4-26b-uncen Q4_K_M | **57.2** (58.0, 56.4) | 1714 (1696, 1732) | riddles 14/14 · HE60 59/60 |
| `f5c0a7a34` (new) | gemma4-26b-uncen Q4_K_M | 55.6 (57.8, 53.5) | 1566 (1213, 1918) | riddles 14/14 · HE60 59/60 |
| `1a33095` (served) | gpt-oss-120b MXFP4 MoE | **51.4** (53.1, 51.2, 49.9) | 1137 (1136, 1160, 1116) | — |
| `f5c0a7a34` (new) | gpt-oss-120b MXFP4 MoE | 51.7 (53.0, 51.2, 51.0) | 1195 (1159, 1213, 1213) | — |

**Verdict: not adopted.** Decode is flat to −2.8 % across two weight classes (a 4B-active 26B and a 5B-active
120B MoE), prefill is noise in one arm and +5 % in the other, and quality is identical item for item on the
60-item probe. The two headline changes do not reach this backend's hot path for these graphs. The prefill
spread inside a single arm (1213 → 1918 t/s) is the shader-cache cold start, and the served build's own reps
drift 53.1 → 49.9 under sustained 120B load — which is why the decision rests on paired reps, not on the best
one.

That is the useful part of a negative result: the matrix stays on **one build identity**, §9's rows stay
comparable, and the next person can read this instead of spending two hours rebuilding to find out. The A/B
runs themselves are archived outside the catalogue (`~/runs/ab-build-ab-20261101/`) so they cannot pollute the
per-model "best run" selection with 60-item probes.

### 4.3 Rebuilt on 2026-11-08 — registered, not measured

Four trees were rebuilt in a seven-minute sweep on the evening of 2026-11-08. **None of them has produced a
row in this report**, and they are recorded here because a rebuild is the event that dates a build register
and the gap between what is served and what exists is now visible in two dimensions at once — commit date and
ggml ABI.

```
   tree                 commit      server build string                      ggml    built
   ───────────────────────────────────────────────────────────────────────────────────────────
   upstream-llama.cpp   7d7f028     0.9.0-dev (build 661, commit 7d7f028)    0.29.0  11-08 22:15
   flint-llama.cpp      7d7f028     0.9.0-dev (build 274, commit 7d7f028)    0.29.0  11-08 22:17
   sensenova-llama.cpp  7d7f028     0.9.0-dev (build 323, commit 7d7f028)    0.29.0  11-08 22:19
   prism-llama.cpp      6447906bf   0.7.0-dev (build 12115, commit 6447906bf) 0.27.0  11-08 22:22
   ───────────────────────────────────────────────────────────────────────────────────────────
   halo-box-strix (fork) 1a3309516  0.5.0-dev (build 3, commit 1a33095)      0.25.3  10-16 09:33  ← every row in §9
```

- **No row in §9 comes from any of them.** Of the 25 model launch scripts that name a binary, 22 serve
  `halo-box-strix-llama.cpp/build/bin/llama-server`, two serve the `f5c0a7a34` scratch clone of §4.2 and one
  serves the Bolt tree. The register's answer to "what produced this number" does not change, and the
  `measured` windows in the table above still end on 2026-11-08 with `1a3309516`.
- **A rebuild is not a measurement.** The four new binaries have no HumanEval, MMLU-Pro, decode, prefill or
  needle row — they were compiled, not run against the suite. The archive still rests entirely on
  `1a3309516`, a binary dated 2026-10-16; the fork's upstream is now **1,081 commits ahead** of that build
  (it was 1,041 on 2026-11-01, §4.2). Nothing here should be read as the report having been re-measured on a
  newer core.
- **The ABI gap is the part that matters.** 0.25.3 against 0.29.0 is four ggml-vulkan minor versions — the
  same discontinuity that made this register necessary in the first place. A number taken on `7d7f028` would
  be a new measurement on a new flavour, not a correction of the fork's, and by §4.2's standard it would need
  paired repetitions on identical weights and flags before it could claim to be one.
- **Why they appear in a benchmark report at all.** Because a reader who clones one of these trees and builds
  it gets a binary four ggml-ABI minor revisions away from the one every published number came from
  (0.29.0 against the served 0.25.3), and that difference is invisible unless it is written down. The sweep is
  an operational event; it is logged here so the register cannot be read as covering a newer core than it does.

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
model on this machine (mellum21, 111.9 t/s) is mid-pack on knowledge, and the best knowledge model on
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

- **Compare within a cap band.** A score at cap 512 is a lower bound, not a measurement: `qwen38-35b`
  read 0.8537 there and 0.8720 at 4096, and its knowledge row moved 13.3 pp for the same reason. Where
  a row is still a floor, label it as one instead of ranking it.
- **Count the burns.** If 17 of 60 items returned empty after exhausting the budget, the mean
  understates the model. Cite the burn count next to the score or the number lies by omission.

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
   and is still this machine's best vision model. It refuses bare chat-format probes because its template
   expects image content. Preflight is a gate for *chat and agent* use, not a universal quality
   measure. 4. **Empty ≠ wrong.** Riddle failures marked empty are usually budget exhaustion, not
   misunderstanding. Check the content, not just the verdict. 5. **Speed is measured alone.** These
   numbers were taken with nothing else on the GPU. Concurrent benchmarks halve decode throughput —
   one model measured 19.5 t/s under contention and 46.9 t/s alone.

**Conventions used throughout.** Speeds appear as `t/s` inside tables and diagrams and as "tokens
per second" in prose; they are the same unit. `pp` is prefill (prompt processing) and `tg` is decode
(token generation). Scores are proportions in 0-1, not percentages. `HE` abbreviates HumanEval, and
The conventions from §0 hold here: compact `MMLU` means MMLU-Pro, never the 14,000-item original. A
"cap-burn" is an item that produced no answer because it exhausted its generation budget. Section numbers
written as §n refer to this document.

**How much difference is real.** Both capability axes are samples, so a gap smaller than about two standard
errors is not evidence of anything. Use this table before ranking two adjacent rows:

| items | SE at p≈0.9 | SE at p≈0.75 | gap worth arguing about |
|---:|---:|---:|---:|
| 164 (HumanEval full) | ±2.3 pp | ±3.4 pp | ≥ 5 pp |
| 120 (MMLU-Pro full) | ±2.7 pp | ±4.0 pp | ≥ 6 pp |
| 60 | ±3.9 pp | ±5.6 pp | ≥ 9 pp |
| 40 | ±4.7 pp | ±6.8 pp | ≥ 11 pp |
| 30 | ±5.5 pp | ±7.9 pp | ≥ 13 pp |

That is why the table carries `items@cap` in every cell and why a 2-item move at n=164 (§9.1's `Ornith-1.5-35B`
re-measure) was reported as noise rather than as an improvement.

Two forward pointers: **§10** states what may and may not be inferred from one model to another in
the same family, and **§5.1-5.6** cover quantisation, which is the variable most often confused with
model quality in comparisons of this kind.

---

## 9. Results — the measured matrix

*Ranked per axis instead? [Leaderboards by axis](leaderboards.html) — same rows, one axis per table, each
carrying its cap and build.*

One row per model that completed the full suite and reached a verdict — 37 of the 75 model aliases that have
at least one measurement in the archive. `HE` is `score (items@cap)`; caps differ, so read
section 7.3 before ranking. Prefill/decode are single-tenant measurements. Every row also has a build
identity — the flavour and commit that produced it — tabulated in §4.1, and recorded per run from
2026-10-27 onwards. The `build` column names the tree and the commit that produced the row — `fork b3-1a33095`, `bolt
b1-a30fb49`, or `pre-identity` where the run predates identity stamping (§4.1 explains why that is a
window, not a guess). The full path is deliberately not published. The `measured` column is the date of the best-scoring run shown — the run id and the full build
identity are in `data/catalogue.json`, so any row can be traced to the exact binary that produced it.
The `disk` column is the roster as of **2026-11-03**: `✓` present and servable,
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
| nemotron-super-120b | 123.6B | Q3_K_M | 0.9512 (164@4096) | 0.7667 (120@4096) | 11/14 | 411 | 27.1 | 2026-10-18 | bolt pre-identity | ✗ 11-05 |
| Nemotron-Bolt-74B-A9B | 74.0B | IQ2_XXS | 0.9451 (164@2048) | 0.3667 (120@2048) | 13/14 | 577 | 72.8 | 2026-10-16 | bolt pre-identity | ✗ 10-30 |
| qwen3next-q6 | 79.7B | Q6_K | 0.9296 (142) | 0.6058 (104) | 14/14 | 1189 | 45.8 | 2026-10-10 | fork pre-identity | ✓ |
| gptoss | 116.8B | MXFP4 | 0.9268 (164) | 0.5833 (120) | 12/14 | 1045 | 50.1 | 2026-10-12 | fork pre-identity | ✓ |
| gptoss-abliterated | 116.8B | MXFP4 | 0.9268 (164@2048) | 0.7500 (120@2048) | 10/14 | 1052 | 50.5 | 2026-10-13 | fork pre-identity | ✓ |
| qwen35 | 122.1B | Q4_K_M | 0.9242 (66) | 0.5417 (48) | 12/14 | 622 | 22.9 | 2026-10-11 | fork pre-identity | ✗ |
| ornith-mtp-21g | 35.5B | IQ4_XS | 0.9207 (164@4096) | 0.7750 (120@2048) | 11/14 | 1610 | 65.2 | 2026-10-17 | fork pre-identity | ✓ |
| flint (i1-Q4_K_M) | 40.0B | Q4_K_M | 0.9167 (60@4096) | — | 10/14 | — | 71.1 | 2026-10-25 | flint pre-identity | ✗ 10-30 |
| Swift-1.5-FN-Heretic | 176.9B | IQ3_S | 0.9167 (60@2048) | 0.8000 (40@2048) | 11/14 | 512 | 25.6 | 2026-11-05 | fork b3-1a33095 | ✓ |
| qwen3next-q4 | 79.7B | Q4_K_M | 0.9146 (164@2048) | 0.7417 (120@2048) | 14/14 | 1219 | 58.1 | 2026-10-31 | fork b3-1a33095 | ✓ |
| mellum21-fork | 12.1B | Q4_K_M | 0.9146 (164@8192) | 0.8083 (120@8192) | 10/14 | 2723 | 111.9 | 2026-10-18 | fork pre-identity | ✗ 11-05 |
| Groot-65B-A6B | 116.5B | Q4_K_M | 0.9000 (60@2048) | 0.7500 (40@2048) | 9/14 | 597 | 27.6 | 2026-11-05 | bolt b1-a30fb49 | ✗ 11-05 |
| mellum | 12.1B | Q6_K | 0.8780 (164@4096) | 0.7000 (120@4096) | 11/14 | 2442 | 91.8 | 2026-10-12 | fork pre-identity | ✗ 10-29 |
| qwen38-35b | 35.5B | Q4_K_M | 0.8720 (164@4096) | 0.6417 (120@4096) | 14/14 | 1550 | 74.8 | 2026-11-01 | fork b3-1a33095 | ✓ |
| Laguna-XS-2.1 | 33.4B | Q4_K_M | 0.8667 (60@4096) | 0.7000 (40@8192) | 10/14 | 1321 | 87.7 | 2026-11-06 | fork b3-1a33095 | ✓ |
| Clover-35B-A3B-Preview | 34.7B | Q4_K_M | 0.8598 (164@4096) | 0.4000 (120@4096) | 14/14 | 1461 | 53.7 | 2026-11-03 | clover b1-6b9c0cf | ✗ 11-03 |
| lfm25-24b-a2b | 24.0B | Q4_0 | 0.8537 (164@4096) | 0.6917 (120@4096) | 10/14 | 2930 | 106.6 | 2026-10-17 | fork pre-identity | ✓ |
| Axion-1.0-35B | 34.7B | Q4_K_M | 0.8500 (60@2048) | 0.7750 (40@2048) | 10/14 | 1422 | 76.2 | 2026-11-05 | fork b3-1a33095 | ✓ |
| Lite-Beam-M2.7-229B | 228.7B | IQ2_XXS | 0.8000 (60@4096) | 0.6750 (40@4096) | 10/14 | 261 | 34.1 | 2026-11-08 | fork b3-1a33095 | ✓ |
| Kimi-Linear-48B-A3B-abl | 49.1B | Q4_K_M | 0.7866 (164@8192) | 0.5833 (120@8192) | 13/14 | 1774 | 74.8 | 2026-11-01 | fork b3-1a33095 | ✗ 11-05 |
| qwen38fn-abl | 176.9B | IQ3_S | 0.8476 (164@2048) | 0.8750 (40@2048) | 11/14 | 448 | 52.9 | 2026-10-13 | fork pre-identity | ✓ |
| qwen36-35b | 34.7B | Q4_K_M | 0.8354 (164) | 0.4500 (120) | 12/14 | 1548 | 57.1 | 2026-10-12 | fork pre-identity | ✗ |
| Ornith-1.5-35B | 35.5B | Q4_K_M | 0.8354 (164@4096) | 0.4417 (120@4096) | 13/14 | 1633 | 74.1 | 2026-11-01 | fork b3-1a33095 | ✓ |
| kimi | 49.1B | Q4_K_M | 0.7866 (164@2048) | 0.5500 (120@2048) | 13/14 | 1597 | 67.4 | 2026-10-14 | fork pre-identity | ✗ 10-29 |
| hy-memory-30b-a3b | 30.1B | Q4_K_M | 0.7805 (164@2048) | 0.7250 (120@2048) | 12/14 | 1515 | 74.7 | 2026-10-17 | fork pre-identity | ✗ 10-29 |
| graft-50b-a3b | 50.7B | Q4_K_M | 0.7805 (164@2048) | 0.6583 (120@2048) | 14/14 | 1368 | 54.3 | 2026-10-19 | fork pre-identity | ✗ |
| hy-memory-30b-a3b-q8 | 30.1B | Q8_0 | 0.7683 (164@2048) | 0.7500 (120@2048) | 11/14 | 1459 | 52.3 | 2026-10-17 | fork pre-identity | ✗ 10-29 |
| Ling-3.0-flash | — | Q4_K_M | — | 0.7667 (120@2048) | 11/14 | — | 43.5 | 2026-10-22 | fork pre-identity | ✗ 10-30 |
| qwen38fn32-prune2 | 32.2B | QMix, 3 banks | — | — | — | 397 | 20.0 | 2026-11-03 | qwen4exp-var b1-1844325 | ✗ 11-03 |
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
capability row. Full inventory (16 model families across 37 .gguf files — 7 projectors and 2 drafters
included — 647 GiB) is in §20.3.

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
| qwen38-35b | Q4_K_M | 0.8720 (164@4096) | 0.6417 (120@4096) | 14/14 | 74.8 | 2026-11-01 | fork b3-1a33095 | :8093 |
| lfm25-24b-a2b | Q4_0 | 0.8537 (164@4096) | 0.6917 (120@4096) | 10/14 | 106.6 | 2026-10-17 | fork pre-identity | :8181 |
| Kimi-Linear-48B-A3B-abl | Q4_K_M | 0.7866 (164@8192) | 0.5833 (120@8192) | 13/14 | 74.8 | 2026-11-01 | fork b3-1a33095 | :8086 |
| qwen38fn-abl | IQ3_S | 0.8476 (164@2048) | invalid (1/120) | 11/14 | 52.9 | 2026-10-13 | fork pre-identity | :8097 |
| Ornith-1.5-35B | Q4_K_M | 0.8354 (164@4096) | 0.4417 (120@4096) | 13/14 | 74.1 | 2026-11-01 | fork b3-1a33095 | :8086 |
| ornith35b (uncensored) | IQ3_XXS | 0.5671 (164@4096) | 0.6333 (120@4096) | 12/14 | 69.9 | 2026-10-31 | fork b3-1a33095 | :8094 boot |

*Retired since this snapshot (2026-11-05): `mellum21-fork`, `Groot-65B-A6B`, `nemotron-super-120b` and
`Kimi-Linear-48B-A3B-abl`; added since it: `Lite-Beam-M2.7-229B` (2026-11-08, :8182 lazily, no unit). The
`:8189` and `:8086` endpoints above are no longer bound and the roster stands at 16 model families. The rows
stay: a snapshot that silently shrinks is not a snapshot.*

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

**nemotron-super-120b — biggest and least ergonomic.** 123.6B at Q3_K_M, 0.9512 code, 0.7667 MMLU,
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
measures 0.9333, which is one of the best instruction scores on this machine.

**Kimi-Linear-48B-A3B-abl — the long-context file, and the honest version of a retired one.** The
abliterated i1-Q4_K_M build (27.66 GiB, 49.1B with ~3B active) measures **0.7866 code, 0.5833
knowledge, 13-14/14 riddles at 74.8 t/s** — the same code score, item for item, as the safety-tuned
`kimi` retired on 2026-10-29 (0.7866 / 0.5500 at 67.4 t/s), so the uncensoring cost nothing measurable
and this file is 10% faster. What it buys is **native context: 1,048,576 tokens**, the only
million-token window on this roster, and that is the reason to keep 28 GiB of a model that two smaller
ones beat on both scored axes.

One constraint travels with it: `n_embd_head_v = 72` does not divide a q8_0 cache block of 32, and the
model refuses mismatched K/V cache types, so the KV cache must be **f16 on both sides**. At ctx 131072
that does not fit beside the 15.6 GiB driver; **ctx 65536 does** (GTT 59.5 of 100 GiB) and is what the
published row was measured at. The full million-token window therefore needs the driver stopped.

**hy-memory-30b-a3b — retired 2026-10-29.** 74.7 t/s, 0.7805 code, 0.7250 MMLU, and a Q8 variant
that raised knowledge to 0.7500 while dropping to 52.3 t/s. Retired as a redundant 30B: 17 GiB for a
knowledge row 12.5 pp behind the 26B driver at two-thirds the speed. The Q4/Q8 pair remains the
cleanest quant-ladder datapoint in the archive (§10.3).

**qwen38-35b / qwen36-35b / ornith35b / Ornith-1.5-35B — the 35B trough.** All four land between
0.82 and 0.87 code with mediocre knowledge and 57-75 t/s. They are not bad; they are simply
dominated by the 26B MoE (faster and better) and the 122B (slower but much better).

Two of the four were re-measured at cap 4096 on 2026-11-01, and the two verdicts differ on **which
axis** the cap was suppressing. `qwen38-35b` gained 3 HumanEval items (0.8537 → **0.8720**) but
**16 MMLU items** (0.5083 → **0.6417**, +13.3 pp, ≫ SE at n=120) and its riddles went 13/14 → 14/14:
for that model the 512 cap was cutting off reasoning before the answer, and the damage showed up in
knowledge far more than in code. `Ornith-1.5-35B` (Q4_K_M) gained 2 HumanEval items (0.8232 →
**0.8354**) and 3 knowledge items (0.4167 → **0.4417**, +2.5 pp, inside SE) — a row that was close to
honest already, and whose remaining weakness is the model, not the budget. So the
lesson is not "512 understates" or "512 is fine": it is that the cap's damage is **axis-dependent**,
and a single axis read at 512 cannot tell you which case you are in.

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

**Clover-35B-A3B-Preview — diffusion pretraining, AR-mode prices.** The box's first diffusion-language
model: a Qwen3.6-35B-A3B finetune under arch `clover_moe`, 34.7B at Q4_K_M, served from its own upstream
tree because no local tree registers the arch. Code lands at **0.8598 (141/164) at cap 4096** with zero
items at the cap — one standard error above its base family's 0.8354 — and knowledge at **0.4000
(48/120)**, base-family level, while the driver reads 0.9512 / 0.8417 at 48.9 t/s against this file's
53.7. Its riddles print 14/14, but three of those returned exactly 4096 tokens on the zebra puzzles and
matched their own restatement, so the committed rate is 11/14. The one thing that would have made it
interesting — parallel, self-speculative diffusion decode — is an unmerged upstream PR, so what was
measured is the AR fallback at AR prices. Deleted 2026-11-03.

**Groot-65B-A6B — a 116.5B model that is honest about its size.** The name says 65B; the header says
116,514,464,640 parameters — 48 blocks, 256 experts routed 10 per token, 12 full-attention layers and 36
Gated DeltaNet layers, under `qwen4exp` with a per-layer embedding bank. At Q4_K_M that is 79.07 GiB on
disk plus a 4.89 GiB draft head, the largest file in this archive, and the first one that does **not** fit
all-resident: pinned that way it held 71.0 GiB of GTT with about 1 GiB available, and a first attempt at
four slots (32k context, vision projector loaded) was globally OOM-killed after seven minutes. With the
fork's `--lazy-mode auto` it settles at 50.4 GiB and serves beside the driver and the boot model at no
decode cost — 27.66 against 27.43 t/s over three greedy samples — which is why it is on disk at all.

Code lands at **0.9000 (54/60 at cap 2048)** and knowledge at **0.7500 (30/40)**; both are subsets, ranked
with their item counts shown, and comparable only to other subsample rows such as flint's 60-item figure.
Decode is **27.6 t/s**, roughly 1.8x slower than the 116.8B gpt-oss file at similar active size, and
instruction-following is the soft axis — IFEval 0.60 prompt-strict and 0.56 instruction-strict over 30
items, against 0.93 for Qwen3-Next-80B. Its bundled MTP head is the one clean speed win in the archive:
**27.66 → 35.66 t/s, +28.7%, 76.3% acceptance**, the exact opposite of every grafted draft head tried here.
Riddles read 9/14, but all five misses returned precisely the 2048 cap with no content at all; re-asked at
4096 the family-relations puzzle answers correctly after 1,953 thinking tokens, so that row measures
deliberation length rather than capability. Kept, not adopted: the driver still wins on code, knowledge,
instruction-following and speed.

**Axion-1.0-35B — the fastest thing per gigabyte.** A brand-new Qwen3.6-shape MoE (`qwen35moe`,
34.66B, roughly A3B) from Axion1-0, Apache-2.0, with a paper pitching open agent foundation models.
At Q4_K_M it is 19.71 GiB and decodes at **76.2 t/s** with 1422 t/s prefill — nothing else in the
20 GiB class pairs 0.8500 code (51/60) with 0.7750 knowledge (31/40) at that rate: qwen38-35b is
74.8 t/s with 0.6417 knowledge, Ornith-1.5-35B 74.1 t/s with 0.4417. Instruction-following is where
it *looks* broken and is not: IFEval reads 0.27 prompt-strict at the harness's pinned 1280-token
generation limit and 0.73 when the constraint is allowed 4096. The mechanism is deliberation, not
refusal — asked directly for "a sentence about a dog without using the letter e" it ran 3,010 tokens
and then answered correctly. Riddles 10/14, every miss capped at 2048. Kept: for 20 GiB it is the
best all-round number on the board.

**Swift-1.5-Flash-Next-Heretic — the abl's twin, measured properly.** A Heretic V2 abliteration of
Qwen3.8-Flash-Next at IQ3_S (176.9B, 78.78 GiB): the same architecture, the same footprint and the
same slot as the resident `qwen38fn-abl`. Benched bare it reads 25.6 t/s, which looked like half the
abl's rate and is not — with the MTP head both files already ship against, Swift runs at **54.63 t/s
against the abl's 55.39** (88.1% acceptance, mean draft length 3.64). A dead heat on speed. At
matched item counts Swift takes code (0.9167 against 0.8667) and instruction-following (0.87 against
0.77 prompt-strict); the abl takes knowledge (0.8750 against 0.8000). Three items each way at n=60/40
is inside one standard error, so this is a tie with opposite strengths rather than a replacement: the
resident file keeps its slot and Swift sits on disk as an unhooked spare, ready for code-heavy work.

**A correction to the abl's knowledge row.** `qwen38fn-abl` has carried "invalid (1/120)" for MMLU-Pro
since 2026-10-13. Re-measured at 40 items, same build, same bare-letter method, it scores 0.8750
(35/40) — the highest knowledge figure in this table. The old cell recorded a harness outcome, not
what the model knows.

**Laguna-XS-2.1 — fastest file on the box, and the cap story a third time.** poolside's agentic-coding MoE
(33B total / 3B active, 256 experts top-8, 10 global + 30 sliding-window layers, 262k ctx, OpenMDW-1.1)
at Q4_K_M is 18.88 GiB and serves beside the driver and the boot unit at GTT 48.7 GiB. **87.7 t/s decode and
1321 t/s prefill are the highest of any full-suite row here** — 15% more decode than Axion's, for a slightly larger
file. Its capability needed a bigger budget than the suite's default. Code went 0.7000 at cap 2048 → **0.8667 at 4096**,
ten items gained, and of the eight remaining misses **six were still cap-pinned** with only two wrong answers,
so its code ceiling is close. Knowledge needed more again: **0.6000 (2048) → 0.6750 (4096) → 0.7000 (8192)**,
and at 8192 the thirteen misses split six cap-pinned, six genuinely wrong — the curve is flattening, so ~0.70 is
where this model's knowledge actually sits. Reading the 2048 row as a verdict would have understated its code by
16.7 pp and its knowledge by 10 pp. IFEval 0.77 prompt-strict /
0.84 instruction-strict at the harness's 1280 pin is the best instruction-following of any non-driver row after Swift;
riddles 10/14. Every cap arm is recorded: `~/bench/runs/humaneval-20261106-192625.jsonl` (4096) and
`mmlupro-20261106-194159.jsonl` / `mmlupro-20261106-200654.jsonl` (4096, 8192). The same weights in BF16 are a trap on this platform: neither serving tree compiles coopmat2
shaders, BF16 matmul takes the generic path, and the file measures **11.6 t/s** — it was deleted the same day, along
with a DFlash draft head that will not load (expected 64 tensors, got 58).

**Lite-Beam M2.7 229B-A10B — the most parameters measured here, at two bits per weight.** MiniMax-M2.7 shape
(228.69B total, A10B active) exported as a mixed **IQ2_XXS at 2.0625 bpw**, split across two shards:
61.36 GiB, 204,800-token training context, served at 16,384. It does not fit all-resident beside the driver,
so it runs lazily (`--load-mode mmap --lazy-mode auto`) on its own port: **34.1 t/s decode, 261 t/s prefill**,
TTFT 7.0 s on a 1,826-token prompt, KV cache at q8_0. At a 4096 cap on both capability axes it reads
**0.8000 code (48/60), 0.6750 knowledge (27/40)**, riddles 10/14, preflight 3/3, and retrieves both needles
(2k and 8k); IFEval is 0.20 prompt-strict / 0.16 instruction-strict over 30 items, the weakest
instruction-following of any row that passes preflight. The two-bit export is what costs it: the 176.9B
`qwen38fn-abl` at IQ3_S scores 0.8476 code and 0.8750 knowledge at 52.9 t/s in 78.78 GiB, so Lite-Beam buys
52B more parameters and 17 GiB less disk for a lower score on both axes and a third less speed. It stays on
disk as the only 200B-class row holding both needles; it takes no slot from anything and nothing takes its.

**qwen38fn32-prune2 — it loads; that was the least of its problems.** The 48.31 GiB export this report
called unloadable in v1.16 does load, on the publisher's own runtime patch, because its 177 "experts" are
three banks (64+60+53, and 154/115 in other blocks) rather than a metadata lie — the v1.16 entry is
corrected. What it then does is worse than not loading: **20.0 t/s decode against 74.8 for the same-shape
Qwen3.8-35B-A3B Distill**, and on Vulkan it degenerates into repetition (`17 * 23 = 17 * 23 = …`, and a
1024-token wall of `/` at the 8k needle) with q8_0 KV *and* with f16 KV and flash-attn off. On the CPU
arm it is fluent and terminates — small arithmetic and instruction-following both fine — but the
knowledge is gone: France and Australia both answer "No", the largest planet is "Earth", 17*23 is "37".
Pruning 3,659 expert slots plus a Q1_0 tier bank cost the facts, and the GPU path never produced correct
output at all. Deleted 2026-11-03.

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
   ornith / qwen3.5  6   0.5610-0.9512 Δ.390   0.4417-0.7917 Δ.350   11-13/14   23-74 t/s
   qwen3.6 / 3.8     7   0.8354-0.8720 Δ.037   0.0083-0.6417 Δ.633   11-14/14   53-75 t/s
   nemotron          3   0.1786-0.9512 Δ.773   0.3667-0.7667 Δ.400    8-13/14   23-73 t/s
   mellum            3   0.8780-0.9146 Δ.037   0.7000-0.8083 Δ.108   10-11/14   92-112 t/s
   gpt-oss           2   0.9268-0.9268 Δ.000   0.5833-0.7500 Δ.167*  10-12/14   50-50 t/s
   hy-memory  ✗      2   0.7683-0.7805 Δ.012   0.7250-0.7500 Δ.025   11-12/14   52-75 t/s
   kimi (linear)     2   0.7866-0.7866 Δ.000   0.5500-0.5833 Δ.033   13-13/14   67-75 t/s
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

## 11. The leaders, in one screen

Four views of the same matrix, reduced to what each axis is actually for. The full ranked tables — every row,
with its cap, item count and build — are on **[Leaderboards by axis](leaderboards.html)**, generated from this
report's own matrix so the two cannot disagree. Retired rows stay in these lists, marked `✗`, because a
leaderboard with the failures removed is how the same 60 GiB gets downloaded twice.

### 11.1 Code — the best coders, and what they cost

| HumanEval | model | status |
|---|---|---|
| 0.9634 @2048 | gemma4-31b | ✗ 10-30 |
| 0.9573 @2048 | gemma4-26b-uncen | ✓ driver |
| 0.9573 @4096 | minicpm-v47-35b | ✓ |

### 11.2 Knowledge — the best on MMLU-Pro

| MMLU-Pro | model | status |
|---|---|---|
| 0.8667 @2048 | gemma4-31b | ✗ 10-30 |
| 0.8667 @2048 | gemma4-26b-a4b | ✗ 10-30 |
| 0.8500 @2048 | gemma4-26b-uncen | ✓ driver |

### 11.3 Throughput — the fastest decoders

| decode | model | status |
|---|---|---|
| 111.9 t/s | mellum21-fork | ✓ |
| 106.6 t/s | lfm25-24b-a2b | ✓ |
| 91.8 t/s | mellum | ✗ 10-29 |

### 11.4 Reasoning traps — models that clear all fourteen

| riddles | model | status |
|---|---|---|
| 14/14 | gemma4-31b | ✗ 10-30 |
| 14/14 | gemma4-26b-uncen | ✓ driver |
| 14/14 | gemma4-26b-a4b | ✗ 10-30 |
| 14/14 | gemma4-26b-qat-q4 | ✓ |
| 14/14 | qwen3next-q6 | ✓ |
| 14/14 | qwen3next-q4 | ✓ |
| 14/14 | qwen38-35b | ✓ |
| 14/14 | graft-50b-a3b | ✗ |

---

What the full tables show that these three do not: the **shape of the roster**. gemma4 owns breadth — the
driver is top-three on code, **first on knowledge among models still on disk** (the two above it are retired),
and clears all fourteen reasoning traps — at 15.6 GiB. Every other model on disk is
a specialist that wins exactly one axis: minicpm on vision, ornith-122b on generous-cap code, gptoss on 120B
breadth, mellum21 on throughput, qwen3next-q6 on instruction adherence, Kimi on a million-token window. A
model that wins nothing is not on disk, which is why the retired rows stay in the tables instead of vanishing.

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
   gemma4-26b-     minicpm-v47  gemma4-26b   Kimi-Linear     minicpm-v47
   uncen (56.9)    ornith-122b  uncen        (1M native)     -35b
   or mellum21     (64 / 23)    (0.8500)     or lfm25 (1M)   (64.6 t/s)
   (111.9)
```
**Table 6 — Job to axis to model.**

| Job | Axis that governs it | Use | Why |
|---|---|---|---|
| Chat / agent behind a messaging channel | preflight + decode speed + riddles | **gemma4-26b-uncen** | 3/3 preflight, 56.9 t/s, 14/14 traps, 15.6 GiB and it is already the enabled unit on :8100 · non-uncensored fallback **gemma4-26b-qat-q4** |
| Difficult one-shot code | HumanEval at a generous cap | **minicpm-v47-35b** or **ornith-122b** | 0.9573 at cap 4096 / 0.9512 at cap 4096; the 0.9634 gemma4-31b that used to hold this slot was retired 10-30 for being dense and 17 t/s — latency is irrelevant for a single answer, so it is the one job it was still defensible for |
| Bulk classification, extraction, triage | decode speed + instruction strictness | **mellum21-fork** (111.9 t/s) or **lfm25** (106.6) | throughput dominates; both follow short instructions well when given room |
| Document Q&A over 100k-1M tokens | context + retrieval, not knowledge | **Kimi-Linear-48B-A3B-abl (1M native)** or **lfm25-24b-a2b (1M option)** | Kimi carries a native 1,048,576-token window at 74.8 t/s, the largest on this machine; lfm25 is faster and scores higher on both axes, so it wins when the 1M window is an option rather than a requirement. Neither is a knowledge model — see their MMLU rows |
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

The question a buyer has is not which chip is fastest, but **which constraint binds first**. On this workload
there are three, and they rank in a fixed order: capacity decides whether a model runs at all, bandwidth
decides how fast it decodes once it runs, and software decides which engines can run on it. The three
platforms answer those questions in a different order, and each one's weakness is the price of its strength.

The evidence here is deliberately asymmetric, and the asymmetry is stated rather than hidden: every number
about this box is measured and traceable to `data/catalogue.json`; every number about the other two is a
vendor specification, cited below, and **not benchmarked for this report**. No RTX card and no Mac was run
here, and nothing below should be read as a head-to-head measurement.

### 13.1 Three definitions of "the GPU's memory"

The platforms differ less in their silicon than in what that phrase means, and in who owns the decision when
the model does not fit.

Figure 12 — Three platforms, three memory models.

```
                        STRIX HALO             NVIDIA (RTX 4090/5090)    APPLE (M-series Max/Ultra)
   ──────────────────────────────────────────────────────────────────────────────────────────────
   Memory                128 GB LPDDR5X         24 / 32 GB GDDR6X/GDDR7   64-512 GB LPDDR5X
   GPU working set       100 GiB GTT            = VRAM, a hard wall       ~75% of RAM (96 of 128 GB)
   Who sets the cap      kernel param (GTT)     the card you bought       driver default (sysctl)
   Disk -> GPU path      NVMe -> page cache     NVMe -> RAM -> PCIe       NVMe -> page cache
                         -> mapped, no copy     -> VRAM, a copy           -> mapped, no copy
   Bandwidth             ~256 GB/s nominal     1008 / 1792 GB/s          546 / 819 GB/s
   Compute               RDNA 3.5, 40 CU        CUDA + tensor cores       Apple GPU + Neural Engine
   Software              Vulkan (+ partial      CUDA, cuBLAS, TensorRT,   Metal, MPS, MLX
                         ROCm on gfx1151)       vLLM, bitsandbytes
   Power (whole box)     ~45-120 W             450-575 W card alone      ~40-140 W
   Upgrade memory?       no, soldered           another card, not VRAM    no, soldered
   Cost for 100 GB+      ~one laptop            4 cards (no P2P) or an    512 GB Ultra: premium
                                                A100/H100
   ──────────────────────────────────────────────────────────────────────────────────────────────
```

**Nvidia — the copy is the design, and VRAM is the wall.** Weights are staged into VRAM across PCIe: 64 GB/s
bidirectional at Gen4 x16, 128 GB/s at Gen5, so 32 and 64 GB/s in the direction a model load travels. For a
13.4 GiB file that is well under a second of link time, which is why load latency is not the interesting
number here — the wall is that the working set cannot exceed VRAM. Past it there are two options and both are
expensive: a second card, where GeForce exposes no peer-to-peer DMA ([confirmed by
NVIDIA](https://www.tomshardware.com/news/nvidia-confirms-geforce-cards-lack-p2p-support), so a 70B split
across two cards stages through host memory); or CUDA's managed allocator, which does oversubscribe by
migrating pages on fault — at page granularity over PCIe, a latency class away from VRAM bandwidth.

**Apple — the cap is a default, not a wall.** The GPU reads the same DRAM. Metal reports
`recommendedMaxWorkingSetSize` at roughly 75% of RAM — 96 GB on a 128 GB machine — and llama.cpp and Ollama
honour it as a ceiling. `sysctl iogpu.wired_limit_mb=114688` raises it to 112 GiB, which is the documented
fix for the confusing failure where a 90 GiB model "refuses to load for no reason". What cannot be changed is
capacity: the memory is soldered, and the top rung (512 GB on an M3 Ultra) is priced accordingly.

**Strix Halo — the cap is GTT, and the copy never happens.** The GPU maps system DRAM through the GTT
aperture: 100 GiB here against 128 GB installed, with an 8 GiB VRAM carve-out left unused. That aperture is
set by kernel parameters, not by a card. Weights arrive by `mmap`, so the mapped pages *are* the page cache:
a 61 GiB load is a fault-in from NVMe in about ten seconds, not a 61 GiB transfer. Everything that follows in
this report follows from that one property — since nothing has to be copied, file size raises a capacity
question and nothing else.

Compressed to three sentences: **Nvidia asks whether the model fits in VRAM, Apple asks whether it fits under
the wired limit, and this box asks whether it fits in GTT.** Three names for the same question, and only two
of the three answers can be changed after purchase.

*Specifications cited above: [RTX 4090](https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/),
[RTX 5090](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/), [Mac Studio — M4 Max and
M3 Ultra](https://support.apple.com/en-ca/122211), [MacBook Pro M4 Max](https://support.apple.com/en-us/121553);
PCIe figures are the PCI-SIG values for x16 links (64 GB/s at Gen4, 128 GB/s at Gen5, bidirectional).*

### 13.2 What the capacity costs: bandwidth per token

Decode is bandwidth divided by bytes read per token, and that formula is indifferent to whose silicon is
underneath. Only the numerator changes.

- **This box.** The 13.4 GiB QAT file at 59.5 t/s implies **134 GB/s** of effective read bandwidth if the
  active set is ~2.25 GB per token (4B active at 4.5 bpw), and 160-190 GB/s if attention and KV reads push it
  to 2.5-3 GiB — both inside the 120-280 GB/s band §2.2 measures, and both well below the 256 GB/s nominal. A
  prior source measured ~215 GB/s on the same silicon (§23).
- **The same file elsewhere, if it fit.** Bandwidth ratios against this box's nominal: 1008 GB/s is 3.9×,
  1792 is 7.0×, 546 is 2.1×, 819 is 3.2×. Those are ceilings, not predictions: they assume identical bytes
  per token, which holds only for the same file at the same quantisation.
- **Where the ratio is the whole story, and where it is not.** At 24 GB a 4090 holds the 13.4 GiB file with
  room for KV, so on the models both machines can hold, the card wins decode by roughly the bandwidth ratio
  and wins prefill by an order of magnitude. Above ~30B the comparison ends rather than reverses: a 70 GiB
  file does not fit, and the honest Nvidia answer is four cards, host-memory staging and 1.8-2.3 kW.
- **Prefill is not bandwidth-bound, and the gap there is the widest.** With no tensor cores, prompt
  processing runs 350-2900 t/s here against several thousand to tens of thousands on parts with matrix
  acceleration — a 10-50× gap, not 2-7×. At 605 t/s, a 30k-token agent prompt costs ~50 s before the first
  token; short chat prompts hide the problem entirely, long agent prompts cannot.
- **Capacity, concretely.** 24 GB is about a 30B dense model at Q4, or a 30B-A3B MoE with KV room; 32 GB is
  35-40B; 100 GiB of GTT is 120B at Q4 (70 GiB) or 229B at 2 bpw (61 GiB, §9.1); Apple's 64-512 GB spans the
  same range with 2-3× this box's bandwidth at the top. A 128 GB Strix box holds what a four-card GeForce rig
  holds, at a quarter of the bandwidth, a fraction of the power and none of the plumbing.

### 13.3 The software gap is wider than the silicon gap

- **CUDA is a platform, not an API.** cuBLAS, cuDNN, TensorRT-LLM, vLLM, flash-attention and bitsandbytes all
  land there first, and so does every new architecture's kernel work. On this workload that buys prefill,
  continuous batching and multi-user serving — the three things this box is worst at.
- **Metal and MLX are a good platform with a narrower ecosystem.** Vendor-maintained and cohesive; llama.cpp
  and MLX both work well on Apple silicon. They have no CUDA and no TensorRT, and the ports follow the CUDA
  originals rather than leading them.
- **Vulkan plus llama.cpp is the mature path here, and ROCm is partial on gfx1151** (§3.2). The concrete
  consequences: no vLLM, no TensorRT-LLM, no bitsandbytes, and a new architecture arrives when a ggml PR
  merges rather than when a vendor kernel ships. That is why the harness (§7) speaks HTTP to `llama-server`
  and nothing else.
- **The quantisation habit inverts.** On CUDA, Q4 is what you do to fit; here it is also what you do to go
  faster, because decode is bandwidth-bound (§5.1). Measured on one family: Q8_0 at 26.1 GiB decodes 49.4 t/s,
  the QAT Q4_0 at 14.4 GiB decodes 59.5 t/s, and the two are three items apart on MMLU-Pro at n=120 — the
  smaller file is faster, cheaper in memory, and level on knowledge.

### 13.4 Where each one breaks

**Nvidia.** Above VRAM the model does not run slowly, it fails: `CUDA out of memory`, or a managed-memory
oversubscription that faults pages over PCIe on every step. Multi-GPU does not rescue it cheaply, because
GeForce has no peer-to-peer DMA, and the power draw is 450-575 W per card before the host.

**Apple.** Above the wired limit the load fails, often with no error a user can interpret; the fix is a
`sysctl`, and above installed RAM there is no fix. There is no CUDA, so CUDA-only tooling is simply
unavailable, memory cannot be added later, and in a laptop chassis sustained load is limited by thermals
rather than by the chip.

**Strix Halo.** Above 100 GiB of GTT nothing runs, and the edge cases are the interesting ones. The 79 GiB
Groot file, before it was retired, held GTT 71 GiB and still needed `--lazy-mode auto` beside the driver
(§9.1); a 229B model fits only at 2 bpw; CPU load steals decode bandwidth because the pool is shared; and
long prompts are the worst case at 350-2900 t/s. ROCm-only tooling is unavailable or partial.

### 13.5 Choosing between them

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

The honest summary, with the mechanism attached: **Strix Halo buys capacity, Apple buys capacity with
bandwidth, Nvidia buys throughput.** This box is the cheapest way to hold 100 GiB of model in GPU address
space, and it is the wrong choice when the bottleneck is prompt processing, concurrent users, or software
that only exists on CUDA. It is not a slow 4090; it is a different machine that fails on different inputs,
and the failure mode — not the benchmark table — is what should drive the purchase.

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
  comparison would need this machine's power draw over the run, which was not instrumented here. -
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
  point; this machine is quiet and cool under sustained local inference, which is the practical case for
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
measurements confirm it: package power reached 130 W and Tctl 75 °C under load, so this machine was using
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
it looks like a 26.8-point ablation bill against the **0.8354** that the standard `Ornith-1.5-35B`
build scores at the same cap since 2026-11-01. The comparison is now like-for-like on budget, so the
remaining gap is the quantisation rung (3.06 bpw against 4.9) plus the uncensoring tune, and it cannot
be attributed to the cap: re-measuring the standard file at four times its original budget moved two
code items and three knowledge items, not 27 points. What the run does establish
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

**The one cost that is measured:** 155 runs totalling **60.6 hours of benchmark execution**, recorded
run by run in `catalogue.json`, over 2026-10-07 → 2026-11-08. Of the 75 model aliases with at least one
measurement, 16 model families remain
servable and every deletion is recorded in the ledger; the two largest deletion passes alone released
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
| running and supervising | 45 | 60 | 60.6 h of measured execution, ~18 h of per-model setup, re-runs and failed loads |
| analysis and correlation | 30 | 45 | alias-collision audits, cap-floor re-measurements, four external sources compared |
| writing and revision | 50 | 70 | 2,816 lines across seven editions, the ledger, ten captioned figures |
| publishing | 12 | 18 | repository, sanitising gates, Pages, discovery metadata, the two probes |
| **total** | **222** | **318** | ≈ 250-300 h |

Of that total, **40–60 hours were attended by a human** — the rest is machine execution and agent time: the decisions the measurements cannot make — what to
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

Figure 15 — HumanEval pass@1 against decode throughput, 30 models.

### 19.2 Knowledge against decode speed

The same axes with the other quality measure, and a different ranking. Speed buys no knowledge: the
two fastest files (mellum21 at 111.9 t/s, lfm25 at 106.6) read 0.8083 and 0.6917, and the best
knowledge-per-second point on this machine is mellum21, still 5.8pp under the ceiling. That ceiling belongs
to two retired files — the 31B and the Q8_0, both 0.8667 — with the live driver at 0.8500. The 2-bit Bolt load (0.3667) sits visibly detached from the rest of the nemotron family.

*Does not show* the hosted tier, which is deliberately absent (§19.8).

{{svg charts/f16-knowledge-speed.svg}}

Figure 16 — MMLU-Pro against decode throughput, 30 models.

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
1-second samples have rolled up out of the raw window — the figure could no longer be rebuilt. It now
points at the longest full-suite run still inside that window (a 112-minute 48B sweep on 2026-11-01), so
it is reproducible today and will stay so for as long as the raw window lasts. **The lesson is
structural:** a figure whose source ages out does not fail loudly, it silently keeps the last SVG that
found data. This one is now picked from a list of runs that are known to be recent, and the build prints
the run it plotted.

{{svg charts/f23-power-run.svg}}

Figure 23 — CPU package power through the 2026-11-01 Kimi-Linear-48B full suite (112 min, both capability axes).

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
   8181 lfm25-24b-a2b    8182 groot65b-a6b (transient bench unit, on demand)
   8183 swift15-fn-heretic (transient bench unit; on disk, no roster unit)
   8185 ornith-mtp-21g    8186 minicpm-v47-35b
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

### 20.5 Where each file came from

The manifest this report was missing: for every servable artefact, the upstream repository, the licence
its card declares, and whether the bytes on disk are provably the bytes upstream publishes. **Thirteen of
seventeen are verified by sha256 against the repository's own LFS object id** — the same check the fetch
script performs, re-run against the files as they sit on disk now.

| artefact | file | size | upstream | licence (repo card) | provenance |
|---|---|---|---:|---|---|
| gemma4-26b-uncen | `Gemma4-26B-A4B-QAT-Uncensored-HauhauCS-Balanced-Q4_K_M.gguf` | 15.64 GiB | [HauhauCS/Gemma4-26B-A4B-QAT-Uncensored-HauhauCS-Balanced-MTP](https://huggingface.co/HauhauCS/Gemma4-26B-A4B-QAT-Uncensored-HauhauCS-Balanced-MTP) | gemma | ✓ sha256 |
| minicpm-v47-35b | `MiniCPM-V-4_7-35B-A3B-Q6_K.gguf` | 26.56 GiB | **not recorded** | — | unverified |
| gemma4-26b-qat-q4 | `gemma-4-26B_q4_0-it.gguf` | 13.45 GiB | [google/gemma-4-26B-A4B-it-qat-q4_0-gguf](https://huggingface.co/google/gemma-4-26B-A4B-it-qat-q4_0-gguf) | apache-2.0 (card) — Gemma Terms upstream | ✓ sha256 |
| ornith-122b | 2 shards | 74.23 GiB | [unsloth/Ornith-1.5-122B-GGUF](https://huggingface.co/unsloth/Ornith-1.5-122B-GGUF) | — | ✓ sha256 |
| nemotron-super-120b | 2 shards | 61.24 GiB | [unsloth/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-GGUF](https://huggingface.co/unsloth/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-GGUF) | other (NVIDIA card) | ✓ sha256 · **retired 2026-11-05** |
| qwen3next-q6 | 2 shards | 63.81 GiB | [unsloth/Qwen3-Next-80B-A3B-Instruct-GGUF](https://huggingface.co/unsloth/Qwen3-Next-80B-A3B-Instruct-GGUF) | apache-2.0 | ✓ sha256 |
| gptoss | `gpt-oss-120b-MXFP4.gguf` | 59.03 GiB | **not recorded** | apache-2.0 upstream | unverified |
| Laguna-XS-2.1 | `Laguna-XS-2.1-Q4_K_M.gguf` | 18.88 GiB | [poolside/Laguna-XS-2.1-GGUF](https://huggingface.co/poolside/Laguna-XS-2.1-GGUF) | openmdw-1.1 (permissive, commercial use allowed) | ✓ sha256 |
| gptoss-abliterated | `gpt-oss-120b-abliterated.i1-MXFP4_MOE.gguf` | 59.03 GiB | [mradermacher/gpt-oss-120b-abliterated-i1-GGUF](https://huggingface.co/mradermacher/gpt-oss-120b-abliterated-i1-GGUF) | apache-2.0 | ✓ sha256 |
| ornith-mtp-21g | `Ornith-1.5-35B-A3B-Abliterated-MTPv2-21G-ICE.gguf` | 19.42 GiB | [gbuzhf/Ornith-1.5-35B-A3B-Abliterated-MTP-UD-APEX-GGUF](https://huggingface.co/gbuzhf/Ornith-1.5-35B-A3B-Abliterated-MTP-UD-APEX-GGUF) | mit | ✓ sha256 |
| mellum21-fork | `Mellum2.1-12B-A2.5B-Thinking-Q4_K_M.gguf` | 7.52 GiB | [JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF](https://huggingface.co/JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF) | apache-2.0 | ✓ sha256 · **retired 2026-11-05** |
| qwen3next-q4 | `Qwen3-Next-80B-A3B-Instruct-UD-Q4_K_XL.gguf` | 42.90 GiB | [unsloth/Qwen3-Next-80B-A3B-Instruct-GGUF](https://huggingface.co/unsloth/Qwen3-Next-80B-A3B-Instruct-GGUF) | apache-2.0 | ✓ sha256 |
| qwen38-35b | `Qwen3.8-35B-A3B-Distill-Q4_K_M.gguf` | 20.22 GiB | **not recorded** | apache-2.0 (empero-ai card; filename differs there) | unverified |
| lfm25-24b-a2b | `LFM2.5-24B-A2B-QAD-Q4_0.gguf` | 12.65 GiB | [LiquidAI/LFM2.5-24B-A2B-GGUF](https://huggingface.co/LiquidAI/LFM2.5-24B-A2B-GGUF) | other (LFM Open License) | ✓ sha256 |
| Kimi-Linear-48B-A3B-abl | `Kimi-Linear-48B-A3B-Instruct-abliterated-bf16.i1-Q4_K_M.gguf` | 27.66 GiB | [mradermacher/Kimi-Linear-48B-A3B-Instruct-abliterated-bf16-i1-GGUF](https://huggingface.co/mradermacher/Kimi-Linear-48B-A3B-Instruct-abliterated-bf16-i1-GGUF) | mit | ✓ sha256 · **retired 2026-11-05** |
| qwen38fn-abl | 2 shards | 78.10 GiB | **not recorded** | — | unverified |
| Ornith-1.5-35B | `Ornith-1.5-35B-Q4_K_M.gguf` | 20.22 GiB | [ornith-ai/Ornith-1.5-35B-A3B-GGUF](https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B-GGUF) | mit | ✓ sha256 |
| ornith35b (uncensored) | `Ornith-1.5-35B-Uncensored-YMQ-M.gguf` | 15.07 GiB | [zerodigest/Ornith-1.5-35B-Uncensored-YMQ-MTP-GGUF](https://huggingface.co/zerodigest/Ornith-1.5-35B-Uncensored-YMQ-MTP-GGUF) | apache-2.0 | ✓ sha256 |

Four rows are *unverified* because no fetch record survived for them: the MiniCPM-V-4.7 Q6_K file, the
`gpt-oss-120b-MXFP4` base file, `Qwen3.8-35B-A3B-Distill-Q4_K_M`, and the two
`Qwen3.8-Flash-Next-GSQ-RCO-abliterated` IQ3_S shards. They predate this record. Their sha256s are in
[`data/provenance.json`](data/provenance.json), so checking them against whichever repository you believe
they came from is a one-minute job — it is just not a claim this document can make for you.

Two licence notes worth not skimming. `gemma-4-26B_q4_0-it` reports **apache-2.0 on its model card**, while
Gemma models are normally distributed under the Gemma Terms of Use — the card is what is quoted here, and
the discrepancy belongs to the card. `LiquidAI/LFM2.5-24B-A2B-GGUF` declares `other`, which is the LFM Open
License; "other" is not a permission, so read it before commercial use.

Every shard's hash, not just the first: [`data/provenance.json`](data/provenance.json).

## 21. Change log

The full version history lives on its own page: **[change log](changelog.html)** — every correction, the
numbers that forced it, and what the report said before. It is long by design; a correction that hides what
was wrong is not a correction.

The seven most recent entries, in brief:

- **v1.23** — **Lite-Beam M2.7 229B-A10B** (MiniMax-M2.7 shape, A10B) measured at IQ2_XXS — 2.0625 bpw,
  61.36 GiB over two shards, served lazily: **0.8000 code (48/60@4096), 0.6750 knowledge (27/40@4096)**,
  10/14 riddles, preflight 3/3, both needles, 34.1 t/s decode / 261 t/s prefill; IFEval 0.20/0.16 is the
  weakest instruction score on the board. Largest file measured, and it displaces nothing — `qwen38fn-abl`
  beats it on both axes at IQ3_S for 17 GiB more. **Also a process correction:** the run was catalogued on
  2026-11-08 but never written into this report, so the previous edition published a data row and three
  regenerated charts with no prose, leaderboard entry or change-log record behind them; §9 and §18.3 counts
  are now recounted from the catalogue (37 matrix rows, 155 runs, 60.6 h, 75 aliases, 16 servable families),
  Table 4b's last three rows, which had been rendering as literal pipe text since v1.20, are back inside
  their table, and the four trees rebuilt on the evening of 2026-11-08 are tabulated in **§4.3 — registered,
  not measured**: `upstream-llama`, `flint` and `sensenova` at `7d7f028` (0.9.0-dev, ggml ABI 0.29.0),
  `prism` at `6447906bf` (0.7.0-dev, ABI 0.27.0), against the served fork `1a3309516` at ABI 0.25.3. **§13 is
  rewritten** around what caps the GPU's working set — VRAM, Apple's wired limit, GTT — with the disk-to-GPU
  path, per-token bandwidth arithmetic, software gap and failure modes for each; and it corrects v1.22's
  "13.4 GiB per token", which was the file size, not the per-token read (§13.2 now states 134-190 GB/s).

- **v1.22** — **Laguna-XS-2.1** (poolside, 33B/A3B agentic-coding MoE, OpenMDW-1.1) joins at Q4_K_M: **87.7 t/s
  decode and 1321 t/s prefill, the fastest row on the box**, with **0.8667 code (60@4096) and 0.7000 knowledge
  (40@8192)** — 16.7 pp and 10 pp above the same model at cap 2048, where 35 of 308 generations pinned; its
  knowledge curve 0.6000 → 0.6750 → 0.7000 across 2048/4096/8192 has flattened. Its BF16 ran 11.6 t/s (no
  coopmat2 path in either tree) and was deleted.
- **v1.21** — roster pass: five files retired after measurement and a hash check against their repos' LFS
  oids — **Mellum2.1-12B Q4_K_M** 7.52 GiB, the **LFM2.5 DSpark head** 0.62 GiB, **Groot-65B-A6B** 79.07 GiB,
  **Nemotron-3.5-Super-VL-120B** 62.86 GiB and **Kimi-Linear-48B-A3B-abl** 27.66 GiB. 177.7 GiB freed; the
  roster is 15 model families at 629.11 GiB. Every deletion kept its measured row in Table 4 and its
  restore recipe in the ledger.
- **v1.20** — two 2026-11-05 arrivals measured and kept: **Axion-1.0-35B** (0.8500 code / 0.7750 knowledge
  from 19.71 GiB at 76.2 t/s) and **Swift-1.5-Flash-Next-Heretic** (0.9167 / 0.8000, and 54.63 t/s once the
  MTP head it ships against is loaded). The instruction axis was re-measured properly: lm-eval pins IFEval at
  1280 tokens, which understates every thinking model on the board — Axion reads 0.27/0.20 at that pin and
  0.73/0.64 at 4096. `qwen38fn-abl`'s long-standing "invalid (1/120)" MMLU cell is replaced by 0.8750 after a
  clean 40-item re-run on the same build.
- **v1.19** — Groot-65B-A6B measured and kept on demand: 116.5B under a 65B name, **0.9000 code (54/60 at
  cap 2048) / 0.7500 knowledge (30/40)**, 27.6 t/s, and the archive's first real drafter win (bundled MTP
  head, **27.66 → 35.66 t/s** at 76.3% acceptance). The finding that matters is the footprint: it does not
  fit all-resident — GTT 71.0 GiB and one OOM kill — and only serves beside the driver under the fork's
  `--lazy-mode auto`, at 50.4 GiB and no speed cost.
- **v1.18** — Clover-35B-A3B-Preview measured and retired (0.8598 code / 0.4000 knowledge, AR mode only);
  the 32B-A6B "Prune2" export **loads after all** — v1.16's "cannot load" was a tier-0-only read of a
  three-bank expert layout — and was then retired for a split failure: repetition on Vulkan, no factual
  knowledge on CPU.
- **v1.17** — §0 rewritten in plain language (five findings, no jargon), with the technical claims moved to §0.1
  and the report's own limits stated as a paragraph rather than a caveat.
- **v1.16** — Qwen3.8-Flash-Next-32B-A6B "Prune2" cannot load (header says 177 experts, tensors hold 64, the
  router still has 177 rows); recorded as unloadable rather than unmeasured, and deleted. **Superseded by
  v1.18.**

## 22. Credits and tooling

**Measurement.** Every figure here was produced by `~/bench/t20` and the per-axis scripts on the
machine described in §2, run by the operator between 2026-10-07 and 2026-11-05. The numbers come from
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
that answers this machine's traffic, not of the best model on this machine — §9.1 explains why those differ.

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

*Version 1.17 · measurements 2026-10-07 → 2026-11-01; build register (§4.1)
and plotted figures (§19) added 2026-10-27; roster and row corrections 2026-10-30; the Qwen3-Next Q4
capability row 2026-10-31 (§21). Numbers are
reproducible from `~/runs/catalogue.json`; per-model recipes for anything deleted live in
`~/llama-local/RETIRED-models.md`.*

---

*Source, data and build scripts: [github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io](https://github.com/strix-halo-128-benchmarks/strix-halo-128-benchmarks.github.io). Every row above is backed by a run id in [`data/catalogue.json`](data/catalogue.json); corrections are welcome as issues there.*
