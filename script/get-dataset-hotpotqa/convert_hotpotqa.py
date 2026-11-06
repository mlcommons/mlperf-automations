#!/usr/bin/env python3
"""Normalize a HotpotQA split (HF parquet or legacy JSON) into the JSON schema
the agent harness consumes: a list of
    {"_id", "question", "answer", "context": [[title, [sentences...]], ...]}.
"""
import json
import sys


def _from_parquet(src):
    import pandas as pd
    df = pd.read_parquet(src)
    rows = []
    for rec in df.to_dict(orient='records'):
        ctx = rec.get('context')
        if ctx is None:
            titles, sents = [], []
        else:
            titles = ctx.get('title')
            titles = [] if titles is None else list(titles)
            sents = ctx.get('sentences')
            sents = [] if sents is None else list(sents)
        context = [[str(t), [str(x) for x in s]] for t, s in zip(titles, sents)]
        rows.append({
            '_id': rec.get('id') if rec.get('id') is not None else rec.get('_id'),
            'question': rec.get('question', ''),
            'answer': rec.get('answer', ''),
            'context': context,
        })
    return rows


def _from_json(src):
    with open(src) as f:
        return json.load(f)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    rows = _from_parquet(src) if src.endswith('.parquet') else _from_json(src)
    with open(dst, 'w') as f:
        json.dump(rows, f)
    print(f'HotpotQA: wrote {len(rows)} questions -> {dst}')


if __name__ == '__main__':
    main()
