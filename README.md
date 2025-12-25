# MLPerf® Automations and Scripts

[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE.md)
[![Downloads](https://static.pepy.tech/badge/mlcflow)](https://pepy.tech/project/mlcflow)
[![MLC script automation features test](https://github.com/mlcommons/mlperf-automations/actions/workflows/test-mlc-script-features.yml/badge.svg?cache-bust=1)](https://github.com/mlcommons/mlperf-automations/actions/workflows/test-mlc-script-features.yml)
[![MLPerf® Inference ABTF POC Test](https://github.com/mlcommons/mlperf-automations/actions/workflows/test-mlperf-inference-abtf-poc.yml/badge.svg)](https://github.com/mlcommons/mlperf-automations/actions/workflows/test-mlperf-inference-abtf-poc.yml)


Welcome to the **MLPerf® Automations and Scripts** repository! This repository is your go-to resource for tools, automations, and scripts designed to streamline the execution of **MLPerf® benchmarks**—with a strong emphasis on **MLPerf® Inference benchmarks**.

Starting **January 2025**, MLPerf® automation scripts is powered by [MLCFlow](https://github.com/mlcommons/mlcflow) automation interface. This new and simplified framework replaces the previous [Collective Mind (CM)](https://github.com/mlcommons/ck/tree/master/cm), providing a more robust, efficient, and self-contained solution for benchmarking workflows, making MLPerf® automations independent of any external projects. 


---

## 🚀 Key Features
- **Automated Benchmarking** – Simplifies running MLPerf® Inference benchmarks with minimal manual intervention.
- **Modular and Extensible** – Easily extend the scripts to support additional benchmarks and configurations.
- **Seamless Integration** – Compatible with Docker, cloud environments, and local machines.

---

## 🧰 MLCFlow (MLC) Automations

Building upon the robust foundation of its predecessor, the Collective Mind (CM) framework, MLCFlow elevates machine learning workflows by simplifying complex tasks such as Docker container management and caching. Written in Python, the mlcflow package offers a versatile interface, supporting both a user-friendly command-line interface (CLI) and a flexible API for effortless automation script management.

At its core, MLCFlow relies on a single powerful automation, the Script, which is extended by two actions: CacheAction and DockerAction. Together, these components provide streamlined functionality to optimize and enhance your ML workflow automation experience.

---

## 🤝 Contributing
We welcome contributions from the community! To contribute:
1. Submit pull requests (PRs) to the **`dev`** branch.
2. Review our [CONTRIBUTORS.md](here) for guidelines and best practices.
3. Explore more about MLPerf® Inference automation in the official [MLPerf® Inference Documentation](https://docs.mlcommons.org/inference/).

Your contributions help drive the project forward!


---

## 💬 Join the Discussion  
Connect with us on the [MLCommons™ Benchmark Infra Discord channel](https://discord.gg/T9rHVwQFNX) to engage in discussions about **MLCFlow** and **MLPerf® Automations**. We’d love to hear your thoughts, questions, and ideas!  

---

## 📰 Stay Updated  
Keep track of the latest development progress and tasks on our [MLPerf® Automations Development Board](https://github.com/orgs/mlcommons/projects/50/views/7?sliceBy%5Bvalue%5D=_noValue).  
Stay tuned for exciting updates and announcements!  

---

## 📄 License
This project is licensed under the [Apache 2.0 License](LICENSE.md).

---

## 💡 Acknowledgments and Funding
This project is made possible through the generous support of:
- [OctoML](https://octoml.ai)
- [cKnowledge.org](https://cKnowledge.org)
- [cTuning Foundation](https://cTuning.org)
- [GATEOverflow](https://gateoverflow.in)
- [MLCommons™](https://mlcommons.org)

We appreciate their contributions and sponsorship!

---

Thank you for your interest and support in MLPerf® Automations and Scripts!
