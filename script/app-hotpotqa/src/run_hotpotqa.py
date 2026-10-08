#!/usr/bin/env python3
"""HotpotQA multi-hop question-answering benchmark harness for MLC.

Datasets:
  * sample : bundled data/tasks.jsonl (offline, for CI).
  * real   : official HotpotQA dev split downloaded as parquet by mlcflow and
             passed in via MLC_HOTPOTQA_TASK_FILE.

Model backends:
  * mock     : deterministic, offline (dry-run) - no model required.
  * endpoint : OpenAI-compatible chat completions endpoint.
  * hf       : local HuggingFace transformers model (CPU or GPU).

Scoring uses official-style Exact Match (EM) and token-level F1.
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


def normalise(text):
    text = str(text).lower()
    text = "".join(ch for ch in text if ch not in set(string.punctuation))
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    return " ".join(text.split())


def f1_score(pred, gold):
    pred_tokens = normalise(pred).split()
    gold_tokens = normalise(gold).split()
    if not pred_tokens or not gold_tokens:
        return float(pred_tokens == gold_tokens)
    common = Counter(pred_tokens) & Counter(gold_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return 0.0
    precision = num_same / len(pred_tokens)
    recall = num_same / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def _context_to_text(context):
    """Normalise both the bundled ([title, [sents]]) and HF parquet
    ({'title': [...], 'sentences': [[...]]}) context formats to plain text."""
    parts = []
    if isinstance(context, dict) and "title" in context:
        titles = list(context.get("title", []))
        sentences = list(context.get("sentences", []))
        for title, sents in zip(titles, sentences):
            parts.append(f"{title}: {' '.join(sents)}")
    else:
        for entry in context or []:
            title, sents = entry[0], entry[1]
            parts.append(f"{title}: {' '.join(sents)}")
    return "\n".join(parts)


def load_tasks():
    task_file = _env("MLC_HOTPOTQA_TASK_FILE")
    dataset = _env("MLC_HOTPOTQA_DATASET", "sample")
    if not task_file:
        if dataset == "real":
            raise FileNotFoundError(
                "Real dataset selected but MLC_HOTPOTQA_TASK_FILE is not set "
                "(download dependency did not run)")
        task_file = str(Path(__file__).parent.parent / "data" / "tasks.jsonl")
    if not os.path.isfile(task_file):
        raise FileNotFoundError(f"HotpotQA task file not found: {task_file}")

    tasks = []
    if task_file.endswith(".parquet"):
        import pandas as pd
        df = pd.read_parquet(task_file)
        for row in df.to_dict(orient="records"):
            tasks.append(row)
    elif task_file.endswith(".jsonl"):
        with open(task_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    tasks.append(json.loads(line))
    else:  # .json - official HotpotQA is a single JSON list
        with open(task_file, encoding="utf-8") as f:
            tasks = json.load(f)
    return tasks


def make_generator():
    backend = _env("MLC_HOTPOTQA_BACKEND", "mock")
    if backend == "endpoint":
        from openai import OpenAI
        client = OpenAI(base_url=_env("MLC_HOTPOTQA_ENDPOINT_URL") or None,
                        api_key=_env("MLC_HOTPOTQA_API_KEY") or "EMPTY")
        model = _env("MLC_HOTPOTQA_MODEL", "gpt-4o")

        def gen(system, user, max_tokens=128):
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
        model_id = _env("MLC_HOTPOTQA_HF_MODEL",
                        "HuggingFaceTB/SmolLM2-135M-Instruct")
        tok = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(model_id)
        model.eval()

        def gen(system, user, max_tokens=128):
            messages = [{"role": "system", "content": system},
                        {"role": "user", "content": user}]
            prompt = tok.apply_chat_template(
                messages, add_generation_prompt=True, tokenize=False)
            enc = tok(prompt, return_tensors="pt")
            with torch.no_grad():
                out = model.generate(**enc, max_new_tokens=max_tokens,
                                     do_sample=False,
                                     pad_token_id=tok.eos_token_id)
            new_tokens = out[0][enc["input_ids"].shape[1]:]
            return tok.decode(new_tokens, skip_special_tokens=True)
        return gen, backend

    return None, "mock"


def answer(task, generator):
    if generator is None:  # mock: correct on even hash, deterministic
        tid = str(task.get("_id", task.get("id", task.get("question", ""))))
        correct = (sum(ord(c) for c in tid) % 2) == 0
        return task.get("answer", "") if correct else "[mock] unknown"
    system = ("Answer the multi-hop question using only the provided context. "
              "Reply with the short answer only, no explanation.")
    user = (f"Context:\n{_context_to_text(task.get('context'))}\n\n"
            f"Question: {task.get('question', '')}")
    return generator(system, user)


def main():
    num_samples = int(_env("MLC_HOTPOTQA_NUM_SAMPLES", "3") or "3")
    level = _env("MLC_HOTPOTQA_LEVEL")
    setting = _env("MLC_HOTPOTQA_SETTING", "distractor")
    dataset = _env("MLC_HOTPOTQA_DATASET", "sample")
    output_dir = _env("MLC_HOTPOTQA_OUTPUT_DIR") or os.getcwd()

    generator, backend = make_generator()

    tasks = load_tasks()
    if level:
        tasks = [t for t in tasks if str(t.get("level", "")) == level]
    tasks = tasks[:num_samples]
    if not tasks:
        print("ERROR: no tasks selected", file=sys.stderr)
        return 1

    print(f"HotpotQA: {len(tasks)} question(s) | dataset={dataset} "
          f"setting={setting} backend={backend}")

    results = []
    start = time.time()
    for task in tasks:
        predicted = answer(task, generator)
        gold = task.get("answer", "")
        em = float(normalise(predicted) == normalise(gold))
        f1 = f1_score(predicted, gold)
        results.append({
            "_id": task.get("_id", task.get("id")),
            "level": task.get("level"),
            "type": task.get("type"),
            "question": task.get("question"),
            "gold": gold,
            "predicted": predicted,
            "em": em,
            "f1": round(f1, 4),
        })
        print(f"  [{task.get('level', '?')}] EM={em:.0f} F1={f1:.2f}")

    n = len(results)
    summary = {
        "benchmark": "hotpotqa",
        "backend": backend,
        "dataset": dataset,
        "setting": setting,
        "model": _env("MLC_HOTPOTQA_HF_MODEL") if backend == "hf"
        else _env("MLC_HOTPOTQA_MODEL"),
        "num_questions": n,
        "exact_match": round(sum(r["em"] for r in results) / n, 4),
        "f1": round(sum(r["f1"] for r in results) / n, 4),
        "wall_time_sec": round(time.time() - start, 3),
        "results": results,
    }

    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "hotpotqa_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"EM: {summary['exact_match'] * 100:.1f}%  "
          f"F1: {summary['f1'] * 100:.1f}%")
    print(f"Results written to {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
