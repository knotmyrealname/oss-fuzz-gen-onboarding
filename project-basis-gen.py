"""
Creates the Dockerfile, project.yaml, and build.sh for a given github repository and maintainer email

Usage:
    python3 project-basis-gen.py <repo_url> <user_email> [output_dir]

    This script assumes that `setup.sh` has already cloned:
        - oss-fuzz/
        - oss-fuzz-gen/
        - fuzz-introspector/
    into the ./work/ directory.
"""

import os
import sys
import subprocess
import textwrap
import yaml

# -----------------------------------------------------------------------------------------------
# Import OSS-Fuzz-Gen dependencies
# -----------------------------------------------------------------------------------------------
OSS_FUZZ_GEN_PATH = os.path.join(os.getcwd(), "work", "oss-fuzz-gen", "experimental", "build_generator")
if OSS_FUZZ_GEN_PATH not in sys.path:
    sys.path.append(OSS_FUZZ_GEN_PATH)
try:
    from build_script_generator import extract_build_suggestions
    import manager  
except ImportError:
    print("[!] Could not import OSS-Fuzz-Gen modules.")
    print("    Ensure `setup.sh` has been run and oss-fuzz-gen exists under ./work/")
    sys.exit(1)

# -----------------------------------------------------------------------------------------------
def print_usage():
    usage = textwrap.dedent("""
    Creates the Dockerfile, project.yaml, and build.sh for a given GitHub repository and maintainer email

    Usage:
        python3 project-basis-gen.py <repo_url> <user_email> [output_dir]
    """)
    print(usage.strip())

# -----------------------------------------------------------------------------------------------
def generate_project_basis(repo_url: str, user_email: str, work_root="work"):
    repo_name = os.path.basename(repo_url).replace(".git", "")
    repo_dir = os.path.join(work_root, "oss-fuzz-gen", "work", repo_name)
    os.makedirs(repo_dir, exist_ok=True)

    # Clone target project
    print(f"[+] Cloning repository: {repo_url}")
    if not os.path.isdir(os.path.join(repo_dir, ".git")):
        subprocess.run(["git", "clone", "--depth", "1", repo_url, repo_dir], check=True)
    else:
        print("[=] Repository already cloned. Skipping clone step.")

    # Generate build script
    print("[+] Generating build.sh ...")
    suggestions = extract_build_suggestions(repo_dir, "auto-build-")
    if not suggestions:
        raise RuntimeError("No build system detected.")
    build_script, _, build_container = suggestions[0]

    build_path = os.path.join(repo_dir, "build.sh")
    with open(build_path, "w") as f:
        f.write(build_script)
    # Ensure the build.sh is executable
    os.chmod(build_path, 0o755)

    # Generate Dockerfile + project.yaml
    # This version simply calls the functionality in OSS-Fuzz-Gen, which may be modified based on testing results
    print("[+] Generating Dockerfile and project.yaml ...")
    manager.create_clean_oss_fuzz_from_empty(repo_dir, build_container, repo_url)

    # Patch the generated project.yaml with maintainer contact info
    project_yaml = os.path.join(repo_dir, "project.yaml")
    if os.path.isfile(project_yaml):
        try:
            with open(project_yaml, "r") as f:
                data = yaml.safe_load(f) or {}

            # Add or update required OSS-Fuzz fields
            data["primary_contact"] = user_email
            data.setdefault("fuzzing_engines", ["libfuzzer"])
            data.setdefault("sanitizers", ["address", "undefined"])
            data.setdefault("architectures", ["x86_64"])

            with open(project_yaml, "w") as f:
                yaml.dump(data, f, sort_keys=False)

            print(f"[+] Added maintainer email to project.yaml ({user_email})")
        except Exception as e:
            print(f"[=] Warning: Could not update project.yaml: {e}")
    else:
        print("[=] Warning: project.yaml not found after generation.")

    print(f"[+] Created OSS-Fuzz config files (build.sh, project.yaml, Dockerfile) in {repo_dir}")
    return repo_dir

# -----------------------------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] in {"-h", "--help"}:
        print_usage()
        sys.exit(0)

    repo_url = sys.argv[1]
    user_email = sys.argv[2]
    work_root = sys.argv[3] if len(sys.argv) > 3 else "work"

    try:
        generate_project_basis(repo_url, user_email, work_root)
    except Exception as e:
        print(f"\n[!] Error: {e}")
        print("    Run with --help for usage instructions.\n")
        sys.exit(1)

