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
    python3 project_basis_gen.py <repo_url> <user_email> [work_root]

Assumes these repos/folders are present locally:
  - ./oss-fuzz-gen
  - ./oss-fuzz
"""

import os
import sys
import subprocess
import textwrap
import yaml
from logger_config import setup_logger

logger = setup_logger(__name__)

def log(msg: str) -> None:
    logger.info(f"\033[94m{msg}\033[00m")

# -----------------------------------------------------------------------------
# Initialization & Imports
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OSS_FUZZ_GEN_PATH = os.path.join(BASE_DIR, "oss-fuzz-gen")
BUILD_GEN_PATH = os.path.join(OSS_FUZZ_GEN_PATH, "experimental", "build_generator")

if BUILD_GEN_PATH not in sys.path:
    sys.path.append(BUILD_GEN_PATH)

try:
    from build_script_generator import extract_build_suggestions
    import manager
except ImportError:
    log("[!] Could not import OSS-Fuzz-Gen modules.")
    log("    Ensure 'oss-fuzz-gen' exists in this directory.")
    sys.exit(1)


# -----------------------------------------------------------------------------
# Environment Setup
# Create local directories representing root directories used in manager
# -----------------------------------------------------------------------------
def setup_local_env(repo_dir: str) -> str:
    """Create local OUT/SRC/WORK directories and set environment variables."""
    paths = {
        "OUT": os.path.join(repo_dir, "out"),
        "SRC": os.path.join(repo_dir, "src"),
        "WORK": os.path.join(repo_dir, "work_tmp"),
    }
    for p in paths.values():
        os.makedirs(p, exist_ok=True)
    os.environ.update(paths)
    logger.debug(f"Local env set: OUT={paths['OUT']} SRC={paths['SRC']} WORK={paths['WORK']}")
    return paths["OUT"]


# -----------------------------------------------------------------------------
# /out Patch
# non root users cannot modify /out on linux, 
#  so we patch every access to a local /out directory
# -----------------------------------------------------------------------------
class OutPathRedirector:
    """Temporarily redirect /out references inside manager.py to a local folder."""
    def __init__(self, local_out: str):
        self.local_out = local_out
        self._real_makedirs = manager.os.makedirs
        self._real_join = manager.os.path.join

    def _rewrite_path(self, path: str) -> str:
        return path.replace("/out", self.local_out, 1) if path.startswith("/out") else path

    def _safe_makedirs(self, path, *args, **kwargs):
        return self._real_makedirs(self._rewrite_path(path), *args, **kwargs)

    def _safe_join(self, a, *p):
        a = self._rewrite_path(a)
        p = tuple(self._rewrite_path(x) for x in p)
        return self._real_join(a, *p)

    def apply(self):
        manager.os.makedirs = self._safe_makedirs
        manager.os.path.join = self._safe_join
        log(f"[+] Redirecting /out → {self.local_out}")

    def restore(self):
        manager.os.makedirs = self._real_makedirs
        manager.os.path.join = self._real_join


# -----------------------------------------------------------------------------
# Fake BuildWorker used to simulate Docker environment for manager call
# -----------------------------------------------------------------------------
class FakeBuildWorker:
    """Minimal mock of OSS-Fuzz-Gen's BuildWorker"""
    def __init__(self, build_script: str, build_suggestion_obj):
        self.build_script = build_script
        self.build_suggestion = build_suggestion_obj
        self.executable_files_build = {'refined-static-libs': []}


# -----------------------------------------------------------------------------
# Core Logic
# -----------------------------------------------------------------------------
def generate_project_basis(repo_url: str, user_email: str, work_root: str = "work") -> str:
    """Main workflow: clone repo, generate build.sh, invoke OSS-Fuzz-Gen manager, patch project.yaml"""
    repo_name = os.path.basename(repo_url).replace(".git", "")
    repo_dir = os.path.join(work_root, "oss-fuzz-gen", "work", repo_name)
    os.makedirs(repo_dir, exist_ok=True)

    # Clone or reuse existing repo
    if not os.path.isdir(os.path.join(repo_dir, ".git")):
        log(f"[+] Cloning repository: {repo_url}")
        subprocess.run(["git", "clone", "--depth", "1", repo_url, repo_dir], check=True)
    else:
        log("[=] Repository already cloned. Skipping clone step.")

    # Generate build.sh
    log("[+] Detecting build system and generating build.sh ...")
    suggestions = extract_build_suggestions(repo_dir, "auto-build-")
    if not suggestions:
        raise RuntimeError("No build system detected.")
    build_script, _, build_suggestion = suggestions[0]

    build_path = os.path.join(repo_dir, "build.sh")
    with open(build_path, "w") as f:
        f.write(build_script)
    os.chmod(build_path, 0o755)

    # Setup local environment and patch /out usage to a local directory
    local_out = setup_local_env(repo_dir)
    redirector = OutPathRedirector(local_out)
    redirector.apply()

    # Create oss-fuzz projects folder for output of manager
    oss_fuzz_projects = os.path.join(work_root, "oss-fuzz", "projects")
    os.makedirs(oss_fuzz_projects, exist_ok=True)

    log("[+] Generating Dockerfile and project.yaml via OSS-Fuzz-Gen ...")
    try:
        fake_worker = FakeBuildWorker(build_script, build_suggestion)
        manager.create_clean_oss_fuzz_from_empty(
            github_repo=repo_url,
            build_worker=fake_worker,
            language="c++",
            test_dir=oss_fuzz_projects,
        )
    finally:
        redirector.restore()

    # Locate output
    latest_out = max(
        (os.path.join(local_out, d) for d in os.listdir(local_out) if d.startswith("empty-build-")),
        key=lambda p: os.path.getmtime(p),
        default=None,
    )
    if not latest_out:
        raise RuntimeError("Generation succeeded but no 'empty-build-*' folder found under OUT")

    # Update project.yaml
    project_yaml = os.path.join(latest_out, "project.yaml")
    if os.path.isfile(project_yaml):
        with open(project_yaml, "r") as f:
            data = yaml.safe_load(f) or {}
        data.update({
            "primary_contact": user_email,
            "fuzzing_engines": ["libfuzzer"],
            "sanitizers": ["address", "undefined"],
            "architectures": ["x86_64"],
        })
        with open(project_yaml, "w") as f:
            yaml.dump(data, f, sort_keys=False)
        log(f"[+] Updated maintainer email → {user_email}")
    else:
        log("[=] Warning: project.yaml not found in generated output.")

    log(f"[+] Generated OSS-Fuzz config in: {latest_out}")
    return latest_out


# -----------------------------------------------------------------------------
# CLI Entrypoint
# -----------------------------------------------------------------------------
def usage():
    print(textwrap.dedent("""
        Usage:
            python3 project_basis_gen.py <repo_url> <user_email> [work_root]
    """).strip())

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] in {"-h", "--help"}:
        usage()
        sys.exit(0)

    repo_url, user_email = sys.argv[1], sys.argv[2]
    work_root = sys.argv[3] if len(sys.argv) > 3 else "work"

    try:
        generate_project_basis(repo_url, user_email, work_root)
    except Exception as e:
        log(f"\n[!] Error: {e}")
        print("    Run with --help for usage instructions.\n")
        sys.exit(1)

