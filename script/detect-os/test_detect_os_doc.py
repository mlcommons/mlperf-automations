import os
import subprocess
import time

def test_mlc_doc_detect_os():
    folder = os.path.join(os.path.expanduser("~"), "MLC", "repos", "mlcommons@mlperf-automations", "script", "detect-os")
    readme_path = os.path.join(folder, "README.md")
    old_mtime = os.path.getmtime(readme_path) if os.path.exists(readme_path) else 0

    subprocess.run(["mlc", "doc", "script", "--tags=detect-os"], check=True)

    assert os.path.exists(readme_path), "README.md was not generated"
    new_mtime = os.path.getmtime(readme_path)
    assert new_mtime != old_mtime, "README.md was not updated"
