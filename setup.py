from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess
import sys
import os

try:
    import tomllib  # For Python 3.11+
except ImportError:
    import toml  # For older Python versions (requires `pip install toml`)


def get_project_meta(file_path="pyproject.toml"):
    """
    Extracts project metadata from the given pyproject.toml file.

    Args:
        file_path (str): Path to the pyproject.toml file.

    Returns:
        dict: Dictionary containing the project metadata.
    """
    try:
        with open(file_path, "r") as f:
            content_tmp = f.read()
            if 'tomllib' in globals():
                # Use tomllib for Python 3.11+
                project_data = tomllib.loads(content_tmp)
            else:
                # Use toml for older versions
                project_data = toml.loads(content_tmp)

        # Extract metadata under [project]
        project_meta = project_data.get("project", {})
        return project_meta

    except FileNotFoundError:
        raise FileNotFoundError(f"Error: {file_path} not found.")
    except Exception as e:
        raise RuntimeError(f"Error reading {file_path}: {e}")
    return {}


def check_prerequisites():
    """Check if Git and python-venv are installed on the system. """
    try:
        # Check for Git
        subprocess.run(["git", "--version"], check=True,
                       stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        sys.exit(
            "Error: Git is not installed on the system. Please install Git and try again.")

    try:
        # Check for python-venv
        subprocess.run([sys.executable, "-m", "venv", "--help"],
                       check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        sys.exit(
            "Error: python-venv module is not available. Please install it and try again.")


class CustomInstallCommand(install):
    """Custom install command to run a custom command after installation."""

    def run(self):
        # Run the standard install process
        install.run(self)

        # Run custom post-install command
        try:
            print("Running custom post-install command...")
            commit_hash = get_commit_hash()
            import mlc
            branch = os.environ.get('MLC_REPO_BRANCH', 'dev')

            res = mlc.access({'action': 'pull',
                              'target': 'repo',
                              'repo': 'mlcommons@mlperf-automations',
                              'branch': branch,
                              # 'checkout': commit_hash
                              })

            if res['return'] > 0:
                return Exception(
                    f"Return code:{res['return']} with error:{res.get('error')}")

            # subprocess.run(["echo", "Custom command executed!"], check=True)
        except Exception as e:
            sys.exit(f"Error running post-install command: {e}")


def read_file(file_name, default=""):
    if os.path.isfile(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            return f.read().strip()
    return default


def get_commit_hash():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'git_commit_hash.txt'), 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"


# Check prerequisites before setup
check_prerequisites()


# Get project metadata from pyproject.toml
project_meta = get_project_meta()

# Read version from the VERSION file
version = read_file("VERSION", default="0.0.1")

setup(

    name=project_meta.get("name", "mlperf"),
    version=version,
    description=project_meta.get("description", "MLPerf Automations."),
    author=", ".join(a.get("name", "")
                     for a in project_meta.get("authors", [])),
    author_email=", ".join(a.get("email", "")
                           for a in project_meta.get("authors", [])),
    packages=find_packages(),
    install_requires=project_meta.get("dependencies", []),
    python_requires=project_meta.get("python-requires", ">=3.8"),
    cmdclass={
        'install': CustomInstallCommand,
    },
)
