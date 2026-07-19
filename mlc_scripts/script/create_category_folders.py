#!/usr/bin/env python3
"""
Create category-based folder structure with symlinks to scripts.
"""

import os
import yaml
from pathlib import Path
from collections import defaultdict

# Category name to folder name mapping


def category_to_foldername(category):
    """Convert category name to a valid folder name."""
    return category.replace('/', '-').replace(' ', '-').lower()


def normalize_category(category):
    """Normalize category name."""
    if not category:
        return "Uncategorized"
    return category.strip('"').strip("'").strip()


# Category mapping (same as in generate_readme.py)
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
    "MLPerf Automotive": "MLPerf Automotive",
    "MLPerf Inference": "MLPerf Inference",
    "MLPerf Training": "MLPerf Training",
    "MLPerf benchmark support": "MLPerf Inference",
    "Modular AI/ML application pipeline": "Modular AI/ML application pipeline",
    "Modular application pipeline": "Modular AI/ML application pipeline",
    "Modular MLPerf benchmarks": "MLPerf Inference",
    "Modular MLPerf inference benchmark pipeline": "MLPerf Inference",
    "Modular MLPerf inference benchmark pipeline for ABTF model": "MLPerf Inference",
    "Modular MLPerf automotive benchmark pipeline for ABTF models": "MLPerf Automotive",
    "Modular MLPerf training benchmark pipeline": "MLPerf Training",
    "Platform information": "Platform information",
    "Python automation": "Python automation",
    "Remote automation": "Remote automation",
    "Reproduce MLPerf benchmarks": "MLPerf Inference",
    "Reproducibility and artifact evaluation": "Reproducibility and artifact evaluation",
    "ROCM automation": "ROCm automation",
    "Tests": "Tests",
    "TinyML automation": "TinyML automation",
    "Utils": "Utilities",
}


def main():
    script_dir = Path(__file__).parent
    by_category_dir = script_dir / "by-category"

    # Remove old by-category directory if it exists
    if by_category_dir.exists():
        print(f"Removing old {by_category_dir}...")
        import shutil
        shutil.rmtree(by_category_dir)

    # Create by-category directory
    by_category_dir.mkdir(exist_ok=True)

    # Collect scripts by category
    categories = defaultdict(list)

    for item in sorted(script_dir.iterdir()):
        if not item.is_dir() or item.name.startswith('.') or item.name.startswith('_'):
            continue

        # Skip the by-category folder itself
        if item.name == 'by-category':
            continue

        meta_path = item / "meta.yaml"
        if not meta_path.exists():
            continue

        try:
            with open(meta_path, 'r') as f:
                meta = yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Error reading {meta_path}: {e}")
            continue

        category = normalize_category(meta.get('category', 'Uncategorized'))
        category = CATEGORY_MAP.get(category, category)

        categories[category].append(item.name)

    # Create category folders and symlinks
    total_links = 0
    for category, scripts in sorted(categories.items()):
        folder_name = category_to_foldername(category)
        category_folder = by_category_dir / folder_name
        category_folder.mkdir(exist_ok=True)

        # Create a README in the category folder
        readme_path = category_folder / "README.md"
        with open(readme_path, 'w') as f:
            f.write(f"# {category}\n\n")
            f.write(
                f"This folder contains {len(scripts)} scripts in the **{category}** category.\n\n")
            f.write("## Scripts\n\n")
            for script in sorted(scripts):
                f.write(f"- [{script}]({script}/)\n")

        # Create symlinks
        for script_name in scripts:
            link_path = category_folder / script_name
            target_path = Path("..") / ".." / script_name

            try:
                link_path.symlink_to(target_path, target_is_directory=True)
                total_links += 1
            except FileExistsError:
                pass
            except Exception as e:
                print(
                    f"Warning: Could not create symlink for {script_name}: {e}")

    # Create main README for by-category
    main_readme = by_category_dir / "README.md"
    with open(main_readme, 'w') as f:
        f.write("# Scripts by Category\n\n")
        f.write(
            "This directory provides a category-based view of all scripts using symbolic links.\n\n")
        f.write(f"## Categories ({len(categories)})\n\n")
        for category in sorted(categories.keys()):
            folder_name = category_to_foldername(category)
            script_count = len(categories[category])
            f.write(
                f"- [{category}]({folder_name}/) ({script_count} scripts)\n")

    print(f"✓ Created {len(categories)} category folders")
    print(f"✓ Created {total_links} symlinks")
    print(f"✓ Category view available at: {by_category_dir}")


if __name__ == "__main__":
    main()
