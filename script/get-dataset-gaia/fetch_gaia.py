#!/usr/bin/env python3
"""Fetch the (gated) GAIA validation split via HuggingFace `datasets` and write
it as JSONL for the agent harness. Token is read from MLC_AGENT_HF_TOKEN/HF_TOKEN.
"""
import json
import os
import sys


def main():
    out_path = sys.argv[1]
    config = sys.argv[2] if len(sys.argv) > 2 else '2023_all'
    split = sys.argv[3] if len(sys.argv) > 3 else 'validation'

    from datasets import load_dataset
    token = os.environ.get('MLC_AGENT_HF_TOKEN') or os.environ.get('HF_TOKEN')
    ds = load_dataset('gaia-benchmark/GAIA', config, split=split,
                      token=token, trust_remote_code=True)
    n = 0
    with open(out_path, 'w') as f:
        for row in ds:
            f.write(json.dumps(dict(row)) + '\n')
            n += 1
    print(f'GAIA: wrote {n} tasks -> {out_path}')


if __name__ == '__main__':
    main()
