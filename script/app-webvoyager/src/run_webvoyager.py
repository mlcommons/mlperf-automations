#!/usr/bin/env python3
"""WebVoyager agentic web-navigation benchmark harness for MLC.

Datasets:
  * sample : bundled data/tasks.jsonl (offline, for CI).
  * real   : official WebVoyager task set (data/WebVoyager_data.jsonl) plus
             data/reference_answer.json, cloned by mlcflow and passed in via
             MLC_WEBVOYAGER_TASK_FILE / MLC_WEBVOYAGER_REF_FILE.

Model backends:
  * mock     : deterministic, offline (dry-run) - no model required.
  * endpoint : OpenAI-compatible chat completions endpoint.
  * hf       : local HuggingFace transformers model.

Note: the official WebVoyager metric uses a GPT-4V judge over live browser
screenshots. Without that environment this harness runs a single-shot planning
step and, when reference answers are available, reports a soft answer-overlap
match (token-F1 >= 0.3) as an approximate signal.
"""
import json
import os
import re
import string
import sys
import time
from collections import Counter
from pathlib import Path


def _env(name, default=""):
    return os.environ.get(name, default).strip()


def _normalise(text):
    text = str(text).lower()
    text = "".join(ch for ch in text if ch not in set(string.punctuation))
    return " ".join(text.split())


def _f1(pred, gold):
    pt, gt = _normalise(pred).split(), _normalise(gold).split()
    if not pt or not gt:
        return 0.0
    common = Counter(pt) & Counter(gt)
    same = sum(common.values())
    if same == 0:
        return 0.0
    p, r = same / len(pt), same / len(gt)
    return 2 * p * r / (p + r)


def load_tasks():
    task_file = _env("MLC_WEBVOYAGER_TASK_FILE")
    dataset = _env("MLC_WEBVOYAGER_DATASET", "sample")
    if not task_file:
        if dataset == "real":
            raise FileNotFoundError(
                "Real dataset selected but MLC_WEBVOYAGER_TASK_FILE is not set")
        task_file = str(Path(__file__).parent.parent / "data" / "tasks.jsonl")
    if not os.path.isfile(task_file):
        raise FileNotFoundError(f"WebVoyager task file not found: {task_file}")
    tasks = []
    with open(task_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))
    return tasks


def load_references():
    ref_file = _env("MLC_WEBVOYAGER_REF_FILE")
    if not ref_file or not os.path.isfile(ref_file):
        return {}
    with open(ref_file, encoding="utf-8") as f:
        raw = json.load(f)
    refs = {}
    for web_name, block in raw.items():
        for ans in block.get("answers", []):
            refs[f"{web_name}--{ans.get('id')}"] = ans.get("ans", "")
    return refs


def make_generator():
    backend = _env("MLC_WEBVOYAGER_BACKEND", "mock")
    if backend == "endpoint":
        from openai import OpenAI
        client = OpenAI(base_url=_env("MLC_WEBVOYAGER_ENDPOINT_URL") or None,
                        api_key=_env("MLC_WEBVOYAGER_API_KEY") or "EMPTY")
        model = _env("MLC_WEBVOYAGER_MODEL", "gpt-4o")

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
        model_id = _env("MLC_WEBVOYAGER_HF_MODEL",
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
    num_samples = int(_env("MLC_WEBVOYAGER_NUM_SAMPLES", "3") or "3")
    max_steps = int(_env("MLC_WEBVOYAGER_MAX_STEPS", "15") or "15")
    website = _env("MLC_WEBVOYAGER_WEBSITE")
    dataset = _env("MLC_WEBVOYAGER_DATASET", "sample")
    output_dir = _env("MLC_WEBVOYAGER_OUTPUT_DIR") or os.getcwd()

    generator, backend = make_generator()
    references = load_references()

    tasks = load_tasks()
    if website:
        tasks = [t for t in tasks if t.get("web_name", "").lower() == website.lower()]
    tasks = tasks[:num_samples]
    if not tasks:
        print("ERROR: no tasks selected", file=sys.stderr)
        return 1

    print(f"WebVoyager: {len(tasks)} task(s) | dataset={dataset} "
          f"backend={backend} references={'yes' if references else 'no'}")

    results = []
    start = time.time()
    for task in tasks:
        tid = str(task.get("id", ""))
        ref = references.get(tid)
        if generator is None:
            steps = min(max_steps, 3 + (len(task.get("ques", "")) % 5))
            success = (sum(ord(c) for c in tid) % 3) != 0
            answer = f"[mock] simulated plan for {tid}"
            soft_f1 = None
        else:
            system = ("You are a web-navigation agent. Given a task and target "
                      "website, state the concrete answer or the first action "
                      "you would take. Be concise.")
            user = f"Website: {task.get('web')}\nTask: {task.get('ques')}"
            answer = generator(system, user)
            steps = 1
            if ref:
                soft_f1 = _f1(answer, ref)
                success = soft_f1 >= 0.3
            else:
                soft_f1 = None
                success = bool(answer)
        results.append({
            "id": tid,
            "web_name": task.get("web_name"),
            "question": task.get("ques"),
            "answer": answer,
            "reference": ref,
            "soft_f1": None if soft_f1 is None else round(soft_f1, 4),
            "success": success,
            "steps": steps,
        })
        print(f"  [{task.get('web_name', '?')}] "
              f"{'PASS' if success else 'FAIL'} ({steps} steps)")

    passed = sum(1 for r in results if r["success"])
    scored = [r for r in results if r["soft_f1"] is not None]
    summary = {
        "benchmark": "webvoyager",
        "backend": backend,
        "dataset": dataset,
        "model": _env("MLC_WEBVOYAGER_HF_MODEL") if backend == "hf"
        else _env("MLC_WEBVOYAGER_MODEL"),
        "num_tasks": len(results),
        "num_passed": passed,
        "success_rate": round(passed / len(results), 4),
        "num_scored_against_reference": len(scored),
        "avg_soft_f1": round(sum(r["soft_f1"] for r in scored) / len(scored), 4)
        if scored else None,
        "avg_steps": round(sum(r["steps"] for r in results) / len(results), 2),
        "wall_time_sec": round(time.time() - start, 3),
        "results": results,
    }

    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "webvoyager_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Success rate: {summary['success_rate'] * 100:.1f}% "
          f"({passed}/{len(results)})")
    print(f"Results written to {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
