#!/usr/bin/env python3
"""GAIA (General AI Assistants) benchmark harness for MLC.

Datasets:
  * sample : bundled data/tasks.jsonl (offline, for CI).
  * real   : the gated official gaia-benchmark/GAIA dataset, downloaded via
             huggingface_hub using an HF token with access.

Trace types (agent reasoning-trace length): web < rag < deep-research.

Model backends:
  * mock     : deterministic, offline (dry-run) - no model required.
  * endpoint : OpenAI-compatible chat completions endpoint.
  * hf       : local HuggingFace transformers model.
Scoring uses GAIA-style normalised exact match against the gold final answer.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

TRACE_STEPS = {"web": 3, "rag": 8, "deep-research": 20}


def _env(name, default=""):
    return os.environ.get(name, default).strip()


def normalise(ans):
    ans = str(ans).strip().lower()
    ans = re.sub(r"[^\w\s]", "", ans)
    ans = re.sub(r"\s+", " ", ans)
    return ans


def load_tasks():
    task_file = _env("MLC_GAIA_TASK_FILE")
    dataset = _env("MLC_GAIA_DATASET", "sample")
    if not task_file and dataset == "real":
        from huggingface_hub import hf_hub_download
        from huggingface_hub.errors import GatedRepoError
        split = _env("MLC_GAIA_SPLIT", "validation")
        token = _env("MLC_GAIA_HF_TOKEN") or os.environ.get("HF_TOKEN") or None
        try:
            task_file = hf_hub_download(
                repo_id="gaia-benchmark/GAIA",
                filename=f"2023/{split}/metadata.jsonl",
                repo_type="dataset",
                token=token)
        except GatedRepoError:
            raise SystemExit(
                "GAIA is a gated dataset. Request access at "
                "https://huggingface.co/datasets/gaia-benchmark/GAIA and pass a "
                "token with --hf_token=<token> (or set HF_TOKEN).")
    if not task_file:
        task_file = str(Path(__file__).parent.parent / "data" / "tasks.jsonl")
    if not os.path.isfile(task_file):
        raise FileNotFoundError(f"GAIA task file not found: {task_file}")
    tasks = []
    with open(task_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                task = json.loads(line)
                if task.get("Question"):
                    tasks.append(task)
    return tasks


def make_generator():
    backend = _env("MLC_GAIA_BACKEND", "mock")
    if backend == "endpoint":
        from openai import OpenAI
        client = OpenAI(base_url=_env("MLC_GAIA_ENDPOINT_URL") or None,
                        api_key=_env("MLC_GAIA_API_KEY") or "EMPTY")
        model = _env("MLC_GAIA_MODEL", "gpt-4o")

        def gen(system, user, max_tokens=512):
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
        model_id = _env("MLC_GAIA_HF_MODEL", "HuggingFaceTB/SmolLM2-135M-Instruct")
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


def answer(task, generator, trace_type):
    if generator is None:  # mock
        correct = (sum(ord(c) for c in str(task.get("task_id", ""))) % 2) == 0
        return task.get("Final answer", "") if correct else "[mock] uncertain"
    system = ("You are a general AI assistant. Answer with the final answer "
              "only, using the GAIA answer format (a number, a short string, or "
              f"a comma separated list). Trace type: {trace_type}")
    return generator(system, task.get("Question", ""))


def main():
    num_samples = int(_env("MLC_GAIA_NUM_SAMPLES", "3") or "3")
    trace_type = _env("MLC_GAIA_TRACE_TYPE", "web")
    level = _env("MLC_GAIA_LEVEL")
    split = _env("MLC_GAIA_SPLIT", "validation")
    dataset = _env("MLC_GAIA_DATASET", "sample")
    output_dir = _env("MLC_GAIA_OUTPUT_DIR") or os.getcwd()

    if trace_type not in TRACE_STEPS:
        print(f"ERROR: unknown trace_type '{trace_type}'", file=sys.stderr)
        return 1

    generator, backend = make_generator()

    tasks = load_tasks()
    if level:
        tasks = [t for t in tasks if str(t.get("Level", "")) == str(level)]
    tasks = tasks[:num_samples]
    if not tasks:
        print("ERROR: no tasks selected", file=sys.stderr)
        return 1

    print(f"GAIA: {len(tasks)} task(s) | dataset={dataset} trace_type={trace_type} "
          f"split={split} backend={backend}")

    results = []
    start = time.time()
    for task in tasks:
        predicted = answer(task, generator, trace_type)
        gold = task.get("Final answer", "")
        correct = normalise(predicted) == normalise(gold)
        results.append({
            "task_id": task.get("task_id"),
            "level": task.get("Level"),
            "question": task.get("Question"),
            "gold": gold,
            "predicted": predicted,
            "correct": correct,
            "trace_steps": TRACE_STEPS[trace_type],
        })
        print(f"  [L{task.get('Level', '?')}] "
              f"{'CORRECT' if correct else 'WRONG'} "
              f"({TRACE_STEPS[trace_type]} trace steps)")

    correct_n = sum(1 for r in results if r["correct"])
    summary = {
        "benchmark": "gaia",
        "backend": backend,
        "dataset": dataset,
        "model": _env("MLC_GAIA_HF_MODEL") if backend == "hf"
        else _env("MLC_GAIA_MODEL"),
        "trace_type": trace_type,
        "split": split,
        "num_tasks": len(results),
        "num_correct": correct_n,
        "accuracy": round(correct_n / len(results), 4),
        "avg_trace_steps": TRACE_STEPS[trace_type],
        "wall_time_sec": round(time.time() - start, 3),
        "results": results,
    }

    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "gaia_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Accuracy: {summary['accuracy'] * 100:.1f}% "
          f"({correct_n}/{len(results)})")
    print(f"Results written to {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
