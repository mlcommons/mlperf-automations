# MLPerf Automations and Scripts

[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE.md)
[![Downloads](https://static.pepy.tech/badge/mlcflow)](https://pepy.tech/project/mlcflow)
[![MLC Script Automation Test](https://github.com/mlcommons/mlperf-automations/actions/workflows/test-mlc-script-features.yml/badge.svg)](https://github.com/mlcommons/mlperf-automations/actions/workflows/test-mlc-script-features.yml)
[![MLPerf Inference ABTF POC Test](https://github.com/mlcommons/mlperf-automations/actions/workflows/test-mlperf-inference-abtf-poc.yml/badge.svg)](https://github.com/mlcommons/mlperf-automations/actions/workflows/test-mlperf-inference-abtf-poc.yml)


Welcome to the **MLPerf Automations and Scripts** repository! This repository is your go-to resource for tools, automations, and scripts designed to streamline the execution of **MLPerf benchmarks**—with a strong emphasis on **MLPerf Inference benchmarks**.

Starting **January 2025**, MLPerf automation scripts are built on the powerful [MLCFlow](https://github.com/mlcommons/mlcflow) automation interface. This modern interface replaces the earlier [Collective Mind (CM)](https://github.com/mlcommons/ck/tree/master/cm), offering a more robust and efficient framework for benchmarking workflows.


---

## 🚀 Key Features
- **Automated Benchmarking** – Simplifies running MLPerf Inference benchmarks with minimal manual intervention.
- **Modular and Extensible** – Easily extend the scripts to support additional benchmarks and configurations.
- **Seamless Integration** – Compatible with Docker, cloud environments, and local machines.
- **MLCFlow (MLC) Integration** – Utilizes the MLC framework to enhance reproducibility and automation.

---

## 🧰 MLCFlow (MLC) Automations

Building on the foundation of its predecessor, the **Collective Mind (CM)** framework, MLCFlow takes ML workflows to the next level by streamlining complex tasks like Docker container management and caching. The `mlcflow` package, written in Python, provides seamless support through both a command-line interface (CLI) and an API, making it easy to access and manage automation scripts.

### Core Automations
- **Script Automation** – Automates script execution across different environments.
- **Cache Management** – Manages reusable cached results to accelerate workflow processes.


---

## 🤝 Contributing
We welcome contributions from the community! To contribute:
1. Submit pull requests (PRs) to the **`dev`** branch.
2. Review our [CONTRIBUTORS.md](here) for guidelines and best practices.
3. Explore more about MLPerf Inference automation in the official [MLPerf Inference Documentation](https://docs.mlcommons.org/inference/).

Your contributions help drive the project forward!

---

## 📰 News
Stay tuned for upcoming updates and announcements.

---

## 📄 License
This project is licensed under the [Apache 2.0 License](LICENSE.md).

---

## 💡 Acknowledgments and Funding
This project is made possible through the generous support of:
- [OctoML](https://octoml.ai)
- [cKnowledge.org](https://cKnowledge.org)
- [cTuning Foundation](https://cTuning.org)
- [MLCommons](https://mlcommons.org)

We appreciate their contributions and sponsorship!

---

Thank you for your interest and support in MLPerf Automations and Scripts!
