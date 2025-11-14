import harness_gen as harness
import ofgo as main
import os

#harness.generate_harness("gpt-5-mini", "argcomplete", 1)

#harness.consolidate_harnesses("argcomplete", "py", 1)

BASE_DIR = os.path.dirname(__file__)
CONSOLIDATE_DIR = os.path.join(BASE_DIR, "gen-projects")
OSS_FUZZ_PROJECTS_DIR = os.path.join(main.OSS_FUZZ_DIR, "projects")

def test_symlink(project: str):
    persistent_project_dir = os.path.join(CONSOLIDATE_DIR, project)
    project_dir = os.path.join(OSS_FUZZ_PROJECTS_DIR, project)
    os.symlink(persistent_project_dir, project_dir, target_is_directory=True)

test_symlink("argcomplete")