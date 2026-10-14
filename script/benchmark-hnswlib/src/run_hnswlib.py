#!/usr/bin/env python3
"""hnswlib approximate-nearest-neighbor benchmark harness for MLC.

Measures HNSW index build time, query throughput (QPS) and recall@k.

Datasets:
  * synthetic : random float32 vectors; exact ground truth is computed with a
                brute-force numpy search (used for CI / quick runs).
  * real      : an ann-benchmarks-style HDF5 file (train / test / neighbors),
                downloaded by mlcflow and passed in via MLC_HNSWLIB_DATASET_FILE.
                The distance metric is read from the file's 'distance' attribute.
"""
import json
import os
import sys
import time

import numpy as np

# ann-benchmarks 'distance' attribute -> hnswlib space name.
DISTANCE_TO_SPACE = {"euclidean": "l2", "angular": "cosine", "dot": "ip"}


def _env(name, default=""):
    return os.environ.get(name, default).strip()


def _int(name, default):
    return int(_env(name, str(default)) or default)


def brute_force_topk(base, queries, k, metric):
    """Exact top-k neighbor indices for each query via numpy."""
    if metric == "cosine":
        base = base / (np.linalg.norm(base, axis=1, keepdims=True) + 1e-12)
        queries = queries / \
            (np.linalg.norm(queries, axis=1, keepdims=True) + 1e-12)
    if metric in ("ip", "cosine"):
        scores = queries @ base.T           # larger = closer
        idx = np.argpartition(-scores, k - 1, axis=1)[:, :k]
    else:  # l2
        # ||q||^2 - 2 q.b + ||b||^2 ; the ||q||^2 term is constant per row.
        b_sq = (base * base).sum(axis=1)
        scores = -2 * (queries @ base.T) + b_sq[None, :]  # smaller = closer
        idx = np.argpartition(scores, k - 1, axis=1)[:, :k]
    return idx


def recall_at_k(approx_labels, true_neighbors, k):
    hits = 0
    total = 0
    for approx, truth in zip(approx_labels, true_neighbors):
        truth_set = set(int(x) for x in truth[:k])
        hits += len(truth_set & set(int(x) for x in approx[:k]))
        total += len(truth_set)
    return hits / total if total else 0.0


def load_synthetic():
    n = _int("MLC_HNSWLIB_NUM_ELEMENTS", 10000)
    dim = _int("MLC_HNSWLIB_DIM", 128)
    nq = _int("MLC_HNSWLIB_NUM_QUERIES", 1000)
    seed = _int("MLC_HNSWLIB_SEED", 42)
    metric = _env("MLC_HNSWLIB_METRIC", "l2")
    rng = np.random.default_rng(seed)
    base = rng.random((n, dim), dtype=np.float32)
    queries = rng.random((nq, dim), dtype=np.float32)
    k = min(_int("MLC_HNSWLIB_K", 10), n)
    true_neighbors = brute_force_topk(base, queries, k, metric)
    return base, queries, true_neighbors, metric, k


def load_real():
    import h5py
    path = _env("MLC_HNSWLIB_DATASET_FILE")
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"HDF5 dataset not found: {path or '(unset)'}")
    with h5py.File(path, "r") as f:
        base = np.asarray(f["train"], dtype=np.float32)
        queries = np.asarray(f["test"], dtype=np.float32)
        true_neighbors = np.asarray(f["neighbors"])
        distance = f.attrs.get("distance", "euclidean")
    metric = DISTANCE_TO_SPACE.get(str(distance), "l2")
    k = min(_int("MLC_HNSWLIB_K", 10), true_neighbors.shape[1])
    return base, queries, true_neighbors, metric, k


def main():
    import hnswlib

    dataset = _env("MLC_HNSWLIB_DATASET", "synthetic")
    M = _int("MLC_HNSWLIB_M", 16)
    ef_construction = _int("MLC_HNSWLIB_EF_CONSTRUCTION", 200)
    ef = _int("MLC_HNSWLIB_EF", 50)
    num_threads = _int("MLC_HNSWLIB_NUM_THREADS", -1)
    output_dir = _env("MLC_HNSWLIB_OUTPUT_DIR") or os.getcwd()

    if dataset == "real":
        base, queries, true_neighbors, metric, k = load_real()
    else:
        base, queries, true_neighbors, metric, k = load_synthetic()

    n, dim = base.shape
    nq = queries.shape[0]
    ef = max(ef, k)  # ef must be > k for meaningful recall
    print(f"hnswlib: dataset={dataset} metric={metric} N={n} dim={dim} "
          f"queries={nq} k={k} M={M} ef_construction={ef_construction} ef={ef}")

    index = hnswlib.Index(space=metric, dim=dim)
    index.init_index(max_elements=n, ef_construction=ef_construction, M=M)
    index.set_num_threads(num_threads)

    t0 = time.time()
    index.add_items(base, np.arange(n))
    build_time = time.time() - t0

    index.set_ef(ef)
    t0 = time.time()
    labels, _ = index.knn_query(queries, k=k)
    query_time = time.time() - t0

    recall = recall_at_k(labels, true_neighbors, k)
    qps = nq / query_time if query_time > 0 else float("inf")
    build_qps = n / build_time if build_time > 0 else float("inf")

    summary = {
        "benchmark": "hnswlib",
        "dataset": dataset,
        "metric": metric,
        "num_elements": n,
        "dim": dim,
        "num_queries": nq,
        "k": k,
        "M": M,
        "ef_construction": ef_construction,
        "ef": ef,
        "num_threads": num_threads,
        "build_time_sec": round(build_time, 4),
        "build_vectors_per_sec": round(build_qps, 2),
        "query_qps": round(qps, 2),
        "mean_query_latency_ms": round(1000 * query_time / nq, 4),
        "recall_at_k": round(recall, 4),
    }

    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "hnswlib_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Build: {build_time:.3f}s ({build_qps:,.0f} vec/s) | "
          f"QPS: {qps:,.0f} | recall@{k}: {recall * 100:.2f}%")
    print(f"Results written to {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
