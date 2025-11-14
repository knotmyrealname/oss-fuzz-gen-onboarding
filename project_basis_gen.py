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
Creates the Dockerfile, project.yaml, build.sh, (and empty skeleton harnesses) for a given github repository and maintainer email

Usage:
    import project_basis_gen 

    output_path = project_basis_gen.generate_project_basis(<repo_url>, <maintainer_email>, [--model <model>]

Notes:
    - Assumes you have followed the setup guide: USAGE.md
    - model defaults to 'gpt-4o-mini'
"""

import os
import sys
import yaml
import shutil
import subprocess
from logger_config import setup_logger

# -------------------------------------------------------------------
# Constants 
# -------------------------------------------------------------------
BASE_DIR = os.path.dirname(__file__)
OSS_FUZZ_DIR = os.path.join(BASE_DIR, "oss-fuzz")
OSS_FUZZ_GEN_DIR = os.path.join(BASE_DIR, "oss-fuzz-gen")
GEN_PROJECTS_DIR = os.path.join(BASE_DIR, "gen-projects")
DEFAULT_MODEL = "gpt-4o-mini"

# -------------------------------------------------------------------
# Logging functionality
# -------------------------------------------------------------------
logger = setup_logger(__name__)
def log(msg: str) -> None:
    logger.info(f"\033[94m{msg}\033[00m")

# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------
def sanitize_repo_name(repo_url: str) -> str:
    """Extracts an OSS-Fuzz project name (lowercase repo name)."""
    name = os.path.basename(repo_url).replace(".git", "").strip().lower()
    if not name:
        raise ValueError(f"Could not parse repository name from URL: {repo_url}")
    return name

def clean_dir(path: str):
    """Delete a directory/symlink if it exists."""
    if os.path.islink(path):
        os.unlink(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.unlink(path)

def symlink_force(src: str, dst: str):
    """
    Create a symlink, replacing an existing files safely.
    """
    clean_dir(dst)
    os.symlink(os.path.abspath(src), dst)

# -------------------------------------------------------------------
# Runner execution 
# -------------------------------------------------------------------
def run_runner(repo_url: str, repo_name: str, model: str) -> str:
    """
    Calls OSS-Fuzz-Gen’s experimental/build_generator/runner.py 
    Return Value (path to generated files):
        OSS_FUZZ_GEN_DIR/generated-builds-tmp/oss-fuzz-projects/<project>
    """
    
    # Runner command expects repo name as a text file "input.txt"
    input_path = os.path.join(OSS_FUZZ_GEN_DIR, "input.txt")
    with open(input_path, "w") as f:
        f.write(repo_url + "\n")

    tmp_output_dir = os.path.join(OSS_FUZZ_GEN_DIR, "generated-builds-tmp")
    clean_dir(tmp_output_dir)

    cmd = [
        "python3", "-m", "experimental.build_generator.runner",
        "-i", input_path,
        "-o", "generated-builds-tmp",
        "-m", model,
        "--oss-fuzz", OSS_FUZZ_DIR,
    ]

    # Run the oss-fuzz-gen command to create the 3 files
    log(f"Running OSS-Fuzz-Gen for {repo_name} using model: {model}")
    try:
        subprocess.run(cmd, cwd=OSS_FUZZ_GEN_DIR, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Runner failed with exit code {e.returncode}")

    # Locate the generated files
    projects_dir = os.path.join(tmp_output_dir, "oss-fuzz-projects")
    if not os.path.isdir(projects_dir) or not os.listdir(projects_dir):
        raise RuntimeError("No generated build directories found — check OSS-Fuzz-Gen output")
    
    # TODO: Test this to confirm functionality
    #
    # Assumes OSS-Fuzz-Gen builds follow the format:
    #   <project>-empty-build-0
    dirs = os.listdir(projects_dir)
    if not dirs:
        raise RuntimeError("OSS-Fuzz-Gen produced no builds")
    candidates = [
        d for d in dirs if d.lower().startswith(repo_name)
    ]

    if not candidates:
        raise RuntimeError(
            f"No generated directory matched repo '{repo_name}'. Found: {dirs}"
        )

    # Take empty-build-0
    candidates.sort()
    chosen = candidates[0]

    output_path = os.path.join(projects_dir, chosen)
    log(f"Generated project basis directory: {output_path}")

    return output_path 
# -------------------------------------------------------------------
# Copy and patch functions
# -------------------------------------------------------------------
def copy_outputs(src_dir: str, dst_dir: str) -> None:
    """Copy Dockerfile, build.sh, and project.yaml into the dst directory."""
    clean_dir(dst_dir)
    os.makedirs(dst_dir, exist_ok=True)

    copied = []
    for fname in ("Dockerfile", "build.sh", "project.yaml"):
        src = os.path.join(src_dir, fname)
        dst = os.path.join(dst_dir, fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            copied.append(fname)
    if not copied:
        raise RuntimeError("No output found in generated directory")
    log(f"Copied: {', '.join(copied)} to {dst_dir}")

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
def generate_project_basis(repo_url: str, email: str, model: str = DEFAULT_MODEL) -> str:
    """
    Calls function to generate the 3 basis files
    Copies the output out of oss-fuzz-gen and into out_dir.
    Patches the project.yaml with email as primary_contact
    """

    repo_name = sanitize_repo_name(repo_url)

    # Path to be returned of generated files
    out_dir = os.path.join(GEN_PROJECTS_DIR, repo_name)

    # Symlink 
    oss_fuzz_project_symlink = os.path.join(OSS_FUZZ_DIR, "projects", repo_name)

    log(f"[+] Starting OSS-Fuzz basis generation for {repo_name}")
    
    # Call oss-fuzz-gen's 'runner' for build generation: Get the path of the generated files
    generated_dir = run_runner(repo_url, repo_name, model)

    # Copy output and patch yaml
    copy_outputs(generated_dir, out_dir)
    patch_project_yaml(os.path.join(out_dir, "project.yaml"), email)
    
    # Make the symlink to files in oss-fuzz
    os.makedirs(os.path.join(OSS_FUZZ_DIR, "projects"), exist_ok=True)
    symlink_force(out_dir, oss_fuzz_project_symlink)

    log(f"Generation complete for {repo_name}")
    log(f"Output saved under: {out_dir}")
    log(f"Symlinked into OSS-Fuzz: {oss_fuzz_project_symlink}")
    
    return out_dir
