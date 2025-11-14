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

import sys
import os
import re
import logging
import time
import subprocess
import shutil

sys.path.insert(0, "./oss-fuzz-gen")
import run_all_experiments
import ofgo as main

## Variable declaration
BASE_DIR = os.path.dirname(__file__)
BENCHMARK_HEURISTICS = "far-reach-low-coverage,low-cov-with-fuzz-keyword,easy-params-far-reach"
NUMBER_OF_HARNESSES = 2
NUM_SAMPLES = 2
WORK_DIR = os.path.join(BASE_DIR, "results")
REPORT_DIR = os.path.join(BASE_DIR, "report")
CONSOLIDATE_DIR = os.path.join(BASE_DIR, "gen-projects")
OSS_FUZZ_PROJECTS_DIR = os.path.join(main.OSS_FUZZ_DIR, "projects")
GENERATED_HARNESS_DIR = os.path.join(CONSOLIDATE_DIR, "samples")

logger = logging.getLogger(__name__)

## Dict of supported languages and their file extensions
language_exts = {
    'c': 'c',
    'c++': 'cpp',
    'go': 'go',
    'javascript': 'js',
    'jvm': 'java',
    'python': 'py',
    'ruby': 'rb',
    'rust': 'rs',
    'swift': 'swift'
}

## Cyan
def log(output):
    logger.info(f"\033[96mharness_gen:\033[00m {output}")

def get_ext_from_project(project) -> str:
    project_yaml = os.path.join(OSS_FUZZ_PROJECTS_DIR, project, "project.yaml")

    language = ""
    with open(project_yaml, "r") as f:
        yaml_content = f.read().splitlines()
        for line in yaml_content:
            if line.startswith("language:"):
                language = line.split(":", 1)[1].strip()

    if language in language_exts:
        return language_exts[language]
    elif language != "":
        log("Unable to identify language. Ensure your project.yaml is in oss-fuzz/projects and has a properly configured project.yaml.")
        sys.exit(1)
    else:
        log(f"Language not supported: {language}.")
        sys.exit(1)

def clean_old_harnesses(project):
    '''
    Removes generated harnesses for a given project

    Args:
        project (str): The project to clean up
    
    Returns:
        None
    '''
    log("Cleaning old harnesses")
    consolidated_dir = os.path.join(CONSOLIDATE_DIR, project)
    old_fuzz_target_regex = fr"fuzz_harness-\d\d_\d\d.(.)*"
    for root, dirs, files in os.walk(consolidated_dir):
        for name in files:
            if re.match(old_fuzz_target_regex, name):
                os.remove(os.path.join(consolidated_dir, name))

def generate_harness(model: str, project: str, temperature: float = 0.4):
    '''
    Generates OSS-Fuzz-gen harnesses for a given project using a specified model and temperature.

    Args:
        model (str): The llm model to use for harness generation.
        project (str): The project to generate harnesses for. Expects the file to be at ofgo/
        temperature (float, optional): The temperature setting for the model. Defaults to 0.4.

    Returns:
        None
    ''' 
    
    ## Sets up folders for persistence
    persistent_project_dir = os.path.join(CONSOLIDATE_DIR, project)
    project_dir = os.path.join(OSS_FUZZ_PROJECTS_DIR, project)
    if not os.path.exists(GENERATED_HARNESS_DIR):
        os.makedirs(GENERATED_HARNESS_DIR)
    if not os.path.exists(persistent_project_dir) and os.path.exists(project_dir):
        shutil.move(project_dir, persistent_project_dir)
        os.symlink(persistent_project_dir, project_dir, target_is_directory=True)
    elif os.path.exists(persistent_project_dir):
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
        os.symlink(persistent_project_dir, project_dir, target_is_directory=True)
    else:
        log(f"Cannot find Project folder for {project} at {project_dir} or any generated projects.")
        sys.exit(1)
        
    ## Cleans up existing project folders
    project_dir_regex = fr"{project}-.*-\d*"
    for root, dirs, files in os.walk(GENERATED_HARNESS_DIR):
        for name in dirs:
            if re.match(project_dir_regex, name):
                shutil.rmtree(os.path.join(GENERATED_HARNESS_DIR, name))
    clean_old_harnesses(project)

    log(f'''Beginning OSS-Fuzz-gen harness generation. This may take a long time''')
    start = time.time()
    
    ## Runs OSS-Fuzz-gen with custom params
    subprocess.run([os.path.join(main.OSS_FUZZ_GEN_DIR, "run_all_experiments.py"),
                    f"--model={model}",
                    f"--generate-benchmarks={BENCHMARK_HEURISTICS}",
                    f"--generate-benchmarks-projects={project}",
                    f"--generate-benchmarks-max={NUMBER_OF_HARNESSES}",
                    f"--oss-fuzz-dir={main.OSS_FUZZ_DIR}",
                    f"--temperature={temperature}",
                    f"--work-dir={WORK_DIR}",
                    f"--num-samples={NUM_SAMPLES}"])

    end = time.time()
    log("Completed in %.4f seconds" % (end - start))
    log(f"Your generated harnesses can be found in {project}-{project}..." +
                "as XX.fuzz_target. To use them, you can move them to your main folder and rename them.")

    ## Get report from OSS-Fuzz-gen run
    os.chdir(main.OSS_FUZZ_GEN_DIR)
    subprocess.run(["python","-m", "report.web", "-r", WORK_DIR, "-o", REPORT_DIR])
    log(f"Report Generated in {REPORT_DIR}")
    log(f'''To view the report, either open up the index.html located within in your web browser or run the command:
    python -m http.server -b 127.0.0.1 5000 -d {REPORT_DIR}''')
    log("You may have to change the IP addresss (127.0.0.1) or port (5000) to suit your needs.")

    ## Move generated data to a folder outside oss-fuzz for persistence
    for root, dirs, files in os.walk(OSS_FUZZ_PROJECTS_DIR):
        for name in dirs:
            if re.match(project_dir_regex, name):
                harness_dir = os.path.join(OSS_FUZZ_PROJECTS_DIR, name)
                target_dir = os.path.join(GENERATED_HARNESS_DIR, name)
                shutil.move(harness_dir, target_dir)

def consolidate_harnesses(project: str, sample_num: int = 1):
    '''
    Retrieves generated harnesses for a given project and consolidates them into a single directory (gen-projects) outside of oss-fuzz.

    Args:
        project (str): The OSS-Fuzz project to consolidate generated harnesses for.
        sample_num (int, optional): The sample number to consolidate. Defaults to 1.

    Returns:
        None
    '''

    ## Check if the project exists
    project_dir = os.path.join(OSS_FUZZ_PROJECTS_DIR, project)
    if not os.path.exists(project_dir):
        log(f"Cannot locate project for consolidation at {project_dir}")
        return

    ## Creates directory to consilidate generated harnesses outside of oss-fuzz for easy access and persistence
    consolidated_dir = os.path.join(CONSOLIDATE_DIR, project)
    if not os.path.exists(consolidated_dir):
        if not os.path.exists(CONSOLIDATE_DIR):
            log("No projects found: cannot consolidate")
        shutil.move(project_dir, consolidated_dir)
        os.symlink(consolidated_dir, project_dir, target_is_directory=True)
    
    ## Clean up prevous fuzz targets
    clean_old_harnesses(project)

    file_ext = get_ext_from_project(project)

    ## Tries to copy over generated files for a specific run sample
    project_dir_regex = fr"{project}-.*-\d*"
    num_found = 1
    for root, dirs, files in os.walk(GENERATED_HARNESS_DIR):
        for name in dirs:
            if re.match(project_dir_regex, name):
                source_file = os.path.join(GENERATED_HARNESS_DIR, name, "%02d.fuzz_target" % (sample_num))
                dest_file = os.path.join(consolidated_dir, "fuzz_harness-%02d_%02d.%s" % (sample_num, num_found, file_ext))
                shutil.copyfile(source_file, dest_file)
                num_found += 1