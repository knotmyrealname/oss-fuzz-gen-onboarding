#!/usr/bin/env python3
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
project_basis_gen.py
--------------------
Creates the Dockerfile, project.yaml, and build.sh for a given github repository and maintainer email

Usage:
    python3 project_basis_gen.py <repo_url> <maintainer_email> [--work WORK_ROOT] [--model MODEL]

Example:
    python3 project_basis_gen.py https://github.com/stephenberry/glaze valid@email.com
    python3 project_basis_gen.py https://github.com/stephenberry/glaze valid@email.com --work work --model gpt-4o-mini
Notes:
    - Assumes you have followed the setup guide: USAGE.md
    - work_root defaults to current directory
    - model defaults to 'gpt-4o'
"""

import os
import sys
import yaml
import shutil
import subprocess
import textwrap
import argparse
from datetime import datetime
from logger_config import setup_logger

# -------------------------------------------------------------------
# Logging functionality
# -------------------------------------------------------------------
logger = setup_logger(__name__)

def log(msg: str) -> None:
    logger.info(f"\033[94m{msg}\033[00m")

# -------------------------------------------------------------------
# Core helper functions
# -------------------------------------------------------------------
def run_runner(repo_url: str, work_root: str, model: str) -> str:
    """Calls OSS-Fuzz-Gen’s experimental runner to generate config files, returns the path of the generated files."""
    # Get repo name to fuzz and local paths to oss-fuzz(gen), to pass to runner command
    repo_name = os.path.basename(repo_url).replace(".git", "")
    oss_fuzz_path = os.path.join(work_root, "oss-fuzz")
    oss_fuzz_gen_path = os.path.join(work_root, "oss-fuzz-gen")
    
    # Runner command expects repo name as a text file
    input_path = os.path.join(oss_fuzz_gen_path, "input.txt")
    with open(input_path, "w") as f:
        f.write(repo_url + "\n")

    # generated-builds-tmp will be the output of the program - expected $MODEL to be set as an environment variable
    cmd = [
        "python3", "-m", "experimental.build_generator.runner",
        "-i", "input.txt",
        "-o", "generated-builds-tmp",
        "-m", model,
        "--oss-fuzz", oss_fuzz_path,
    ]

    # Run the oss-fuzz-gen command to create the 3 files
    log(f"Running OSS-Fuzz-Gen for {repo_name} using model: {model}")
    try:
        subprocess.run(cmd, cwd=oss_fuzz_gen_path, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Runner failed with exit code {e.returncode}")

    # Locate the generated files
    gen_dir = os.path.join(oss_fuzz_gen_path, "generated-builds-tmp", "oss-fuzz-projects")
    if not os.path.isdir(gen_dir) or not os.listdir(gen_dir):
        raise RuntimeError("No generated build directories found — check OSS-Fuzz-Gen output")
    
    # Get the latest files for this project
    latest = max((os.path.join(gen_dir, d) for d in os.listdir(gen_dir)), key=os.path.getmtime)
    log(f"Latest generated project: {latest}")
    return latest


def copy_outputs(latest_dir: str, base_out: str) -> None:
    """Copy Dockerfile, build.sh, and project.yaml into the output directory."""
    os.makedirs(base_out, exist_ok=True)
    copied = []
    for fname in ("Dockerfile", "build.sh", "project.yaml"):
        src = os.path.join(latest_dir, fname)
        dst = os.path.join(base_out, fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            copied.append(fname)
    if not copied:
        raise RuntimeError("No output found in generated directory")
    log(f"Copied: {', '.join(copied)} to {base_out}")


def patch_project_yaml(yaml_path: str, email: str) -> None:
    """Update the maintainer email in project.yaml."""
    if not os.path.exists(yaml_path):
        log("project.yaml not found. skipping patch")
        return
    with open(yaml_path, "r") as f:
        y = yaml.safe_load(f) or {}
    y["primary_contact"] = email
    with open(yaml_path, "w") as f:
        yaml.dump(y, f, sort_keys=False)
    log(f"Updated maintainer email to: {email}")


# -------------------------------------------------------------------
# Main workflow
# -------------------------------------------------------------------
def generate_project_basis(repo_url: str, email: str, work_root: str, model: str) -> None:
    """Calls functions to generate the 3 files, copy outputs out of oss-fuzz-gen, and patch the project.yaml"""
    repo_name = os.path.basename(repo_url).replace(".git", "")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base_out = os.path.join(os.getcwd(), "outputs", f"{repo_name}-{timestamp}")

    log(f"[+] Starting OSS-Fuzz basis generation for {repo_name}")
    latest_generated = run_runner(repo_url, work_root, model)
    copy_outputs(latest_generated, base_out)
    patch_project_yaml(os.path.join(base_out, "project.yaml"), email)

    log(f"Generation complete for {repo_name}")
    log(f"Output saved under: {base_out}")


# -------------------------------------------------------------------
# CLI entrypoint
# -------------------------------------------------------------------
def usage():
    """Usage guide passed into --help for argparse"""
    return textwrap.dedent("""
        Usage:
            python3 project_basis_gen.py <repo_url> <maintainer_email> [--work WORK_ROOT] [--model MODEL]

        Example:
            python3 project_basis_gen.py https://github.com/stephenberry/glaze valid@email.com
            python3 project_basis_gen.py https://github.com/stephenberry/glaze valid@email.com --work work --model gpt-4o

        Notes:
            - Assumes you have followed the setup guide: USAGE.md
            - work_root defaults to current directory
            - model defaults to 'gpt-4o'
    """).strip()

def main():
    """Parse arguments as described above, and call generate_project_basis with user input."""
    parser = argparse.ArgumentParser(
        description=usage(),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("repo_url", help="GitHub repository URL")
    parser.add_argument("maintainer_email", help="Maintainer email for project.yaml")
    parser.add_argument(
        "--work",
        dest="work_root",
        default=os.getcwd(),
        help="Optional working directory (default: current directory)",
    )
    parser.add_argument(
        "--model",
        dest="model",
        default="gpt-4o",
        help="OpenAI model name (default: gpt-4o)",
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(0)

    args = parser.parse_args()

    try:
        generate_project_basis(args.repo_url, args.maintainer_email, args.work_root, args.model)
    except Exception as e:
        log(f"Error: {e}")
        sys.exit(1)
    
if __name__ == "__main__":
    main()
