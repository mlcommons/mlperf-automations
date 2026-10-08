#!/usr/bin/env python3
"""WebArena agentic web-task benchmark harness for MLC.

Datasets:
  * sample : bundled data/tasks.jsonl (offline, for CI).
  * real   : official WebArena config set (config_files/test.raw.json), cloned
             by mlcflow and passed in via MLC_WEBARENA_TASK_FILE.

Model backends:
  * mock     : deterministic, offline (dry-run) - no model required.
  * endpoint : OpenAI-compatible chat completions endpoint.
  * hf       : local HuggingFace transformers model.

Note: WebArena's functional evaluators (program_html, url_match) require the
self-hosted WebArena site environment. Without it, this harness scores only the
offline-checkable string_match tasks against their reference answers and marks
the rest as needs_env.
"""
import json
import os
import re
import string
import sys
import time
from pathlib import Path

SITE_ALIASES = {
    "shopping": ["shopping", "shopping_admin"],
    "reddit": ["reddit"],
    "gitlab": ["gitlab"],
    "cms": ["shopping_admin"],
    "map": ["map"],
    "wikipedia": ["wikipedia"],
}


def _env(name, default=""):
    return os.environ.get(name, default).strip()


def _normalise(text):
    text = str(text).lower()
    text = "".join(ch for ch in text if ch not in set(string.punctuation))
    return " ".join(text.split())


def load_tasks():
    task_file = _env("MLC_WEBARENA_TASK_FILE")
    dataset = _env("MLC_WEBARENA_DATASET", "sample")
    if not task_file:
        if dataset == "real":
            raise FileNotFoundError(
                "Real dataset selected but MLC_WEBARENA_TASK_FILE is not set")
        task_file = str(Path(__file__).parent.parent / "data" / "tasks.jsonl")
    if not os.path.isfile(task_file):
        raise FileNotFoundError(f"WebArena task file not found: {task_file}")
    if task_file.endswith(".json"):
        with open(task_file, encoding="utf-8") as f:
            return json.load(f)
    tasks = []
    with open(task_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))
    return tasks


def score_string_match(pred, reference_answers):
    """Return 1.0/0.0 for offline-scorable string_match, or None if not."""
    if not reference_answers:
        return None
    if "exact_match" in reference_answers:
        return float(_normalise(pred) == _normalise(reference_answers["exact_match"]))
    if "must_include" in reference_answers:
        return float(all(_normalise(x) in _normalise(pred)
                         for x in reference_answers["must_include"]))
    return None  # fuzzy_match requires an LLM judge


def make_generator():
    backend = _env("MLC_WEBARENA_BACKEND", "mock")
    if backend == "endpoint":
        from openai import OpenAI
        client = OpenAI(base_url=_env("MLC_WEBARENA_ENDPOINT_URL") or None,
                        api_key=_env("MLC_WEBARENA_API_KEY") or "EMPTY")
        model = _env("MLC_WEBARENA_MODEL", "gpt-4o")

        def gen(system, user, max_tokens=256):
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                max_tokens=max_tokens)
            return resp.choices[0].message.content
        return gen, backend

    if backend == "hf":
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        model_id = _env("MLC_WEBARENA_HF_MODEL",
                        "HuggingFaceTB/SmolLM2-135M-Instruct")
        tok = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(model_id)
        model.eval()

        def gen(system, user, max_tokens=256):
            prompt = tok.apply_chat_template(
                [{"role": "system", "content": system},
                 {"role": "user", "content": user}],
                add_generation_prompt=True, tokenize=False)
            enc = tok(prompt, return_tensors="pt")
            with torch.no_grad():
                out = model.generate(**enc, max_new_tokens=max_tokens,
                                     do_sample=False,
                                     pad_token_id=tok.eos_token_id)
            return tok.decode(out[0][enc["input_ids"].shape[1]:],
                              skip_special_tokens=True)
        return gen, backend

    return None, "mock"


def main():
    num_samples = int(_env("MLC_WEBARENA_NUM_SAMPLES", "3") or "3")
    max_steps = int(_env("MLC_WEBARENA_MAX_STEPS", "30") or "30")
    site = _env("MLC_WEBARENA_SITE")
    dataset = _env("MLC_WEBARENA_DATASET", "sample")
    output_dir = _env("MLC_WEBARENA_OUTPUT_DIR") or os.getcwd()

    generator, backend = make_generator()

    tasks = load_tasks()
    if site:
        allowed = SITE_ALIASES.get(site.lower(), [site.lower()])
        tasks = [t for t in tasks
                 if any(s.lower() in allowed for s in t.get("sites", []))]
    tasks = tasks[:num_samples]
    if not tasks:
        print("ERROR: no tasks selected", file=sys.stderr)
        return 1

    print(f"WebArena: {len(tasks)} task(s) | dataset={dataset} backend={backend}")

    results = []
    start = time.time()
    for task in tasks:
        eval_block = task.get("eval", {})
        eval_types = eval_block.get("eval_types", [])
        if generator is None:
            steps = min(max_steps, 5 + (len(task.get("intent", "")) % 8))
            success = (sum(ord(c) for c in str(task.get("task_id", ""))) % 3) != 0
            answer = f"[mock] simulated completion for {task.get('task_id')}"
            score = float(success)
            needs_env = False
        else:
            system = ("You are a web agent. Answer the user's request about the "
                      "site directly and concisely with the final answer only.")
            user = (f"Sites: {', '.join(task.get('sites', []))}\n"
                    f"Task: {task.get('intent', '')}")
            answer = generator(system, user)
            steps = 1
            if eval_types == ["string_match"]:
                score = score_string_match(answer, eval_block.get("reference_answers"))
                needs_env = score is None
                success = bool(score)
            else:
                score = None
                needs_env = True
                success = False
        results.append({
            "task_id": task.get("task_id"),
            "sites": task.get("sites"),
            "intent": task.get("intent"),
            "eval_types": eval_types,
            "answer": answer,
            "score": score,
            "needs_env": needs_env,
            "success": success,
            "steps": steps,
        })
        tag = "NEEDS-ENV" if results[-1]["needs_env"] else (
            "PASS" if success else "FAIL")
        print(f"  [{'/'.join(task.get('sites', ['?']))}] {tag} ({steps} steps)")

    scored = [r for r in results if r["score"] is not None]
    passed = sum(1 for r in scored if r["success"])
    summary = {
        "benchmark": "webarena",
        "backend": backend,
        "dataset": dataset,
        "model": _env("MLC_WEBARENA_HF_MODEL") if backend == "hf"
        else _env("MLC_WEBARENA_MODEL"),
        "num_tasks": len(results),
        "num_scored": len(scored),
        "num_needs_env": sum(1 for r in results if r["needs_env"]),
        "num_passed": passed,
        "success_rate_scored": round(passed / len(scored), 4) if scored else None,
        "avg_steps": round(sum(r["steps"] for r in results) / len(results), 2),
        "wall_time_sec": round(time.time() - start, 3),
        "results": results,
    }

    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "webarena_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    if scored:
        print(f"Success rate (scored subset): "
              f"{summary['success_rate_scored'] * 100:.1f}% "
              f"({passed}/{len(scored)})")
    print(f"{summary['num_needs_env']} task(s) need the live WebArena environment")
    print(f"Results written to {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
