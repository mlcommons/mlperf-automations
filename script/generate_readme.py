#!/usr/bin/env python3
"""
Generate README.md for MLCommons scripts directory.
Scans all meta.yaml files and organizes scripts by category.
"""

import os
import yaml
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Standard category mapping to ensure consistency
CATEGORY_MAP = {
    "AI/ML datasets": "AI/ML datasets",
    "AI/ML frameworks": "AI/ML frameworks",
    "AI/ML models": "AI/ML models",
    "AI/ML optimization": "AI/ML optimization",
    "Cloud automation": "Cloud automation",
    "Compiler automation": "Compiler automation",
    "CUDA automation": "CUDA automation",
    "Dashboard automation": "Dashboard automation",
    "Detection or installation of tools and artifacts": "Detection or installation of tools and artifacts",
    "DevOps automation": "DevOps automation",
    "Docker automation": "Docker automation",
    "MLC automation": "MLCommons automation",
    "MLC Interface": "MLCommons interface",
    "MLC Script Template": "MLCommons script templates",
    "MLC Sys Utils": "MLCommons system utilities",
    "MLC Utils": "MLCommons utilities",
    "MLPerf benchmark support": "MLPerf benchmark support",
    "Modular AI/ML application pipeline": "Modular AI/ML application pipeline",
    "Modular application pipeline": "Modular AI/ML application pipeline",
    "Modular MLPerf benchmarks": "Modular MLPerf benchmarks",
    "Modular MLPerf inference benchmark pipeline": "Modular MLPerf inference benchmark pipeline",
    "Modular MLPerf inference benchmark pipeline for ABTF model": "Modular MLPerf inference benchmark pipeline",
    "Modular MLPerf automotive benchmark pipeline for ABTF models": "Modular MLPerf inference benchmark pipeline",
    "Modular MLPerf training benchmark pipeline": "Modular MLPerf training benchmark pipeline",
    "Platform information": "Platform information",
    "Python automation": "Python automation",
    "Remote automation": "Remote automation",
    "Reproduce MLPerf benchmarks": "Reproduce MLPerf benchmarks",
    "Reproducibility and artifact evaluation": "Reproducibility and artifact evaluation",
    "ROCM automation": "ROCm automation",
    "Tests": "Tests",
    "TinyML automation": "TinyML automation",
    "Utils": "Utilities",
}


def normalize_category(category):
    """Normalize category name to standard form."""
    if not category:
        return "Uncategorized"
    category = category.strip('"').strip("'").strip()
    return CATEGORY_MAP.get(category, category)


def read_meta_yaml(script_dir):
    """Read and parse meta.yaml file."""
    meta_path = script_dir / "meta.yaml"
    if not meta_path.exists():
        return None
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Error reading {meta_path}: {e}")
        return None


def generate_readme():
    """Generate README.md from all meta.yaml files."""
    repo_root = Path(__file__).parent
    script_dir = repo_root

    if not script_dir.exists():
        print(f"Error: script directory not found at {script_dir}")
        return

    categories = defaultdict(list)

    for item in sorted(script_dir.iterdir()):
        if not item.is_dir() or item.name.startswith('.') or item.name.startswith('_'):
            continue

        meta = read_meta_yaml(item)
        if not meta:
            continue

        script_name = item.name
        display_name = meta.get('name', script_name)
        category = normalize_category(meta.get('category', 'Uncategorized'))
        alias = meta.get('alias', script_name)
        tags = meta.get('tags', [])

        categories[category].append({
            'name': script_name,
            'display_name': display_name,
            'alias': alias,
            'tags': tags,
            'uid': meta.get('uid', ''),
        })

    sorted_categories = sorted(categories.items())

    readme_lines = [
        "# MLCommons Automation Scripts",
        "",
        f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
        "This directory contains automation scripts for MLPerf benchmarks, AI/ML workflows, and development operations.",
        "",
        "## Table of Contents",
        "",
    ]

    for category, _ in sorted_categories:
        anchor = category.lower().replace(' ', '-').replace('/', '')
        readme_lines.append(f"- [{category}](#{anchor})")

    readme_lines.extend(["", "---", ""])

    for category, scripts in sorted_categories:
        readme_lines.append(f"## {category}")
        readme_lines.append("")

        for script in sorted(scripts, key=lambda x: x['name']):
            alias_info = f" (alias: `{script['alias']}`)" if script['alias'] != script['name'] else ""
            readme_lines.append(
                f"- **[{script['name']}]({script['name']}/)**{alias_info}")
            readme_lines.append(f"  - {script['display_name']}")
            if script['tags']:
                tags_str = ', '.join([f"`{tag}`" for tag in script['tags']])
                readme_lines.append(f"  - Tags: {tags_str}")

        readme_lines.append("")

    readme_lines.extend([
        "---",
        "",
        "## Statistics",
        "",
        f"- **Total Scripts**: {sum(len(scripts) for scripts in categories.values())}",
        f"- **Categories**: {len(categories)}",
        "",
        "## Usage",
        "",
        "These scripts are part of the MLCommons automation framework. To use them:",
        "",
        "```bash",
        "# Run a script using its alias",
        "mlc run script <alias> [options]",
        "",
        "# Or directly",
        "cd <script-directory>",
        "./run.sh [options]",
        "```",
        "",
        "For more information about each script, see the `meta.yaml` file in the script directory.",
        "",
    ])

    readme_path = script_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(readme_lines))

    print(f"✓ Generated {readme_path}")
    print(f"  - {sum(len(scripts) for scripts in categories.values())} scripts")
    print(f"  - {len(categories)} categories")


if __name__ == "__main__":
    generate_readme()
