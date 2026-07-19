#!/usr/bin/env python3
# Copyright (c) 2025, NVIDIA CORPORATION. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#           http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Script to preprocess the data for Llama2-70b."""

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from datasets import Dataset

G_MAX_INPUT_TOK_LEN = 2048
G_LLAMA2_EOS = 2


def preprocess_data(data_dir, preprocessed_data_dir):
    data_dir = Path(data_dir)
    preprocessed_data_dir = Path(preprocessed_data_dir)
    preprocessed_data_dir.mkdir(parents=True, exist_ok=True)

    # Load inference data
    inference_pkl_path = data_dir / "open_orca_gpt4_tokenized_llama.sampled_24576.pkl"
    df = pd.read_pickle(inference_pkl_path)
    toks = df['tok_input'].to_list()
    toks_np = np.ones((len(toks), G_MAX_INPUT_TOK_LEN),
                      dtype=np.int32) * G_LLAMA2_EOS
    tok_len_np = df['tok_input_length'].to_numpy().astype(np.int32)

    for i, q in enumerate(toks):
        toks_np[i, :len(q)] = q
        assert len(q) == tok_len_np[i]

    np.save(preprocessed_data_dir / "input_ids_padded.npy", toks_np)
    np.save(preprocessed_data_dir / "input_lens.npy", tok_len_np)

    # Load calibration data
    calib_pkl_path = data_dir / "open_orca_gpt4_tokenized_llama.calibration_1000.pkl"
    calib_df = pd.read_pickle(calib_pkl_path)

    if 'input' not in calib_df.columns:
        raise ValueError("The DataFrame does not contain an 'input' column.")

    hf_dataset = Dataset.from_pandas(calib_df[['input']])
    hf_dataset = hf_dataset.rename_column("input", "text")

    dataset_dir = preprocessed_data_dir / 'mlperf_llama2_openorca_calibration_1k'
    dataset_dir.mkdir(parents=True, exist_ok=True)
    hf_dataset.to_parquet(dataset_dir / "data.parquet")

    logging.info(f"Done preprocessing llama2 at {preprocessed_data_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess Llama2 data for TensorRT")
    parser.add_argument(
        "--data_dir", "-d",
        help="Path to the input open_orca pickle file",
        default="build/data"
    )
    parser.add_argument(
        "--preprocessed_data_dir", "-o",
        help="Output directory for the preprocessed data.",
        default="build/preprocessed_data"
    )
    args = parser.parse_args()

    preprocess_data(args.data_dir, args.preprocessed_data_dir)


if __name__ == "__main__":
    main()
