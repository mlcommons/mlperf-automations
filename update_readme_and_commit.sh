#!/bin/bash
#
# Auto-update script README and commit changes
# This script regenerates the README.md based on current meta.yaml files
# and commits the changes if there are any.
#

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

echo "Updating scripts README..."
python3 script/generate_readme.py

# Check if README.md changed
if git diff --quiet script/README.md; then
    echo "✓ README.md is up to date"
else
    echo "✓ README.md has been updated"
    
    # Stage the README
    git add script/README.md
    
    echo ""
    echo "script/README.md has been staged. You can now commit with:"
    echo "  git commit -m 'Update scripts README'"
    echo ""
    echo "Or to auto-commit:"
    git commit -m "Auto-update scripts README [skip ci]" || echo "Commit failed or no changes to commit"
fi
