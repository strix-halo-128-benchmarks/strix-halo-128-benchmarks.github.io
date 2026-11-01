"""Deterministic graders for the ~/bench suite.

Every grader is deterministic (no model-as-judge): accept-lists, numeric
tolerance, JSON parse, executed code. Reconstructed 2026-10-07.
"""
from __future__ import annotations

import json
import re
import time

import benchlib as bl


# ---------------------------------------------------------------------------
# Preflight: does the server produce non-empty, well-formed, obeying answers?
# ---------------------------------------------------------------------------

def preflight(port: int, max_tokens: int = 256) -> list[dict]:
    probes = [
        ("content_nonempty", "Reply with exactly: OK", None),
        ("json_schema", 'Return a JSON object with exactly one key "status" and value "ok". Nothing else.', "json"),
        ("instruction_one_word", "What is the capital of France? Answer with exactly one word.", "word"),
    ]
    out = []
    for name, prompt, kind in probes:
        try:
            r = bl.chat(port, prompt, max_tokens=max_tokens, temperature=0.0)
        except Exception as e:
            out.append({"task": name, "pass": False, "detail": f"ERROR {e}"})
            continue
        content = r["content"]
        if kind is None:
            ok = bool(content)
        elif kind == "json":
            ok = _parses_json(content)
        elif kind == "word":
            ok = len(content.split()) <= 2 and bool(content)
        out.append({
            "task": name,
            "pass": ok,
            "detail": content[:120].replace("\n", " "),
            "finish": r["finish"],
        })
    return out


def _parses_json(text: str) -> bool:
    # tolerate a leading/trailing fence
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return False
    try:
        json.loads(m.group(0))
        return True
    except json.JSONDecodeError:
        return False


# ---------------------------------------------------------------------------
# Performance: warmup then prefill/decode rates + time-to-first-token
# ---------------------------------------------------------------------------

def perf(port: int, prompt_tokens: int = 2000, max_tokens: int = 128) -> dict:
    # warm up (first prefill after idle is cold)
    bl.chat(port, "Warmup. Reply OK.", max_tokens=16, temperature=0.0)
    time.sleep(0.5)

    # build a ~prompt_tokens prompt (roughly 4 chars/token)
    filler = ("The quick brown fox jumps over the lazy dog. " * 200)
    filler = (filler * (prompt_tokens * 4 // len(filler) + 1))[: prompt_tokens * 4]
    prompt = filler + "\n\nRepeat exactly: ALPHA BRAVO CHARLIE"

    r = bl.chat(port, prompt, max_tokens=max_tokens, temperature=0.0, cache_prompt=False)
    timings = r["raw"].get("timings", {})
    return {
        "prompt_n": r["prompt_n"],
        "completion_n": r["completion_n"],
        "pp_tps": r["pp_tps"],
        "tg_tps": r["tg_tps"],
        "ttft_ms": timings.get("prompt_ms"),
        "wall": r["wall"],
        "content": r["content"][:80].replace("\n", " "),
    }


# ---------------------------------------------------------------------------
# Needle-in-haystack: retrieve a planted fact from the middle of a long context
# ---------------------------------------------------------------------------

def needle(port: int, ctx_tokens: int = 2000, max_tokens: int = 256) -> dict:
    """Retrieval probe with a retry for reasoning models.

    256 tokens, not the original 64: a reasoning model (gpt-oss/Mellum served with
    `--reasoning auto`) spends 50-500+ tokens in its analysis channel before emitting
    `content`, so a small budget returns a truncated non-answer and scores a false FAIL.
    If the model ran out of tokens (finish=='length') without producing the value, retry
    once with 4x the budget — that distinguishes "cannot retrieve" from "ran out of
    thinking budget". Non-reasoning models stop early and never hit the retry.
    """
    needle_val = f"NEEDLE-{ctx_tokens}-{int(time.time()) % 100000}"
    filler = "The history of the ancient kingdom is long and uneventful. " * 40
    filler = (filler * (ctx_tokens * 4 // len(filler) + 1))[: ctx_tokens * 4]
    # plant the needle in the middle
    half = len(filler) // 2
    context = filler[:half] + f" [The secret passphrase is {needle_val}.] " + filler[half:]
    prompt = context + "\n\nWhat is the secret passphrase mentioned above? Answer with just the passphrase."

    r = bl.chat(port, prompt, max_tokens=max_tokens, temperature=0.0, cache_prompt=False)
    retried = False
    if needle_val.lower() not in r["content"].lower() and r["finish"] == "length":
        retried = True
        r = bl.chat(port, prompt, max_tokens=max_tokens * 4, temperature=0.0, cache_prompt=False)
    return {
        "ctx_tokens": ctx_tokens,
        "pass": needle_val.lower() in r["content"].lower(),
        "content": r["content"][:80].replace("\n", " "),
        "finish": r["finish"],
        "retried": retried,
        "prompt_n": r["prompt_n"],
        # kept so a context-scaling run can report the shape of prefill, not just pass/fail
        "pp_tps": r.get("pp_tps"),
        "tg_tps": r.get("tg_tps"),
        "completion_n": r.get("completion_n"),
    }


# ---------------------------------------------------------------------------
# Riddles + arithmetic traps (canonical probe set)
# ---------------------------------------------------------------------------

RIDDLE_PROBES = [
    ("What is full of holes but still holds water?", ["sponge"], "riddle"),
    ("What can you break, even if you never pick it up or touch it?", ["promise"], "riddle"),
    ("What can run but never walks, has a mouth but never talks, has a head but never weeps, has a bed but never sleeps?", ["river"], "riddle"),
    ("The more you take, the more you leave behind. What are they?", ["footstep"], "riddle"),
    ("This thing all things devour; birds, beasts, trees, flowers; gnaws iron, bites steel; grinds hard stones to meal; slays king, ruins town and beats mountain down. What is it?", ["time"], "riddle"),
    ("What is 17 times 23? Answer with just the number.", ["391"], "arith"),
    ("Which is bigger: 9.11 or 9.9? Answer with just the number.", ["9.9"], "arith"),
    ("A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost? Answer with just the number.", ["0.05", "5 cent", "$0.05"], "arith"),
    
    # RiddleBench 2025 - Seating Arrangement (high-difficulty spatial constraint)
    ("There are five houses in a row, each with a different color. The green house is immediately to the left of the white house. The person in the red house drinks coffee. The Dane lives in the blue house. The person who drinks tea lives in the middle house. The Norwegian lives in the first house. The person who smokes Pall Mall has a bird. The person who drinks milk lives next to the person who smokes Dunhill. The person who smokes Blue Master drinks beer. The German smokes Prince. The Norwegian lives next to the yellow house. The person who smokes Blend lives next to the one who keeps cats. Who owns the fish?", ["german"], "riddle"),
    
    # MultiZebraLogic 2026 - 2x3 Zebra Puzzle with Red Herring
    ("There are two houses. Each has a person with a job, a favorite book genre, and a hobby. The nurse lives in house 1. The person who loves fantasy is not in house 1. The person who likes bouldering is the nurse. The person who likes handball does not live in house 2. The romance reader lives in house 2. The person who likes reading fantasy is not the nurse. Who lives in house 2 and what is their hobby?", ["bouldering"], "riddle"),
    
    # RiddleBench 2025 - Blood Relations (multi-step inference)
    ("A is the brother of B. C is the sister of A. D is the mother of C. E is the father of A. F is the daughter of D. Who is F to E?", ["daughter"], "riddle"),
    
    # RiddleBench 2025 - Coding-Decoding (pattern + reversal)
    ("In a code language, 'CAT' is written as 'XZG'. How is 'DOG' written in that code?", ["wlt"], "riddle"),
    
    # MultiZebraLogic 2026 - 4x5 Zebra Puzzle (high complexity)
    ("There are four houses in a row, numbered 1 to 4 from left to right. Each house has a resident with a unique job, favorite drink, favorite animal, and nationality. The Brit lives in house 2. The person who drinks tea is in house 3. The German drinks coffee. The person who owns the dog is in house 1. The person who drinks water is next to the person who owns the cat. The person who drinks milk is in house 4. The person who owns the bird is the one who drinks tea. The person who owns the fish is the one who drinks beer. The Norwegian lives in house 1. The person who owns the horse is the one who smokes Pall Mall. The person who smokes Dunhill lives next to the person who owns the cat. The person who smokes Blue Master drinks beer. The person who smokes Prince lives next to the one who owns the bird. The person who smokes Blend drinks water. Who owns the fish?", ["german"], "riddle"),
    
    # RiddleBench 2025 - Sequential Reasoning (hidden rule)
    ("What comes next in the sequence: 1, 11, 21, 1211, 111221, ?", ["312211"], "riddle"),
]


def riddles(port: int, max_tokens: int = 512) -> list[dict]:
    rows = []
    for prompt, accepts, kind in RIDDLE_PROBES:
        try:
            r = bl.chat(port, prompt, max_tokens=max_tokens, temperature=0.2)
        except Exception as e:
            rows.append({"kind": kind, "pass": False, "detail": f"ERROR {e}", "completion_n": 0, "wall": 0})
            continue
        ok = bl.contains_any(r["content"], accepts)
        rows.append({
            "kind": kind,
            "pass": ok,
            "detail": r["content"][:80].replace("\n", " "),
            "completion_n": r["completion_n"],
            "wall": round(r["wall"], 1),
            "tg_tps": r["tg_tps"],
        })
    return rows
