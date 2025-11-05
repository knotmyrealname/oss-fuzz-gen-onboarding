#!/usr/bin/env python3
# Copyright 2025 Chainguard
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
import logging
import time
import subprocess

sys.path.insert(0, "./oss-fuzz-gen")
import run_all_experiments
import oss_fuzz_gen_onboarding as main

## Variable declaration
BASE_DIR = os.path.dirname(__file__)
BENCHMARK_HEURISTICS = "far-reach-low-coverage,low-cov-with-fuzz-keyword,easy-params-far-reach"
NUMBER_OF_HARNESSES = 1
NUM_SAMPLES = 1
WORK_DIR = os.path.join(BASE_DIR, "results")
REPORT_DIR = os.path.join(BASE_DIR, "report")

logger = logging.getLogger(__name__)

## Cyan
def log(output):
    logger.info(f"\033[96mharness_gen:\033[00m {output}")

def generate_harness(model : str, project : str, temperature : float = 0.4):
    
    ## Checks to make sure project is valid (assumes model has already been checked by main method)
    project_location = os.path.join(main.OSS_FUZZ_DIR, f"projects/{project}")
    if not os.path.exists(project_location):
        log(f"Cannot find Project folder for {project} at {project_location}")

    log(f'''Beginning OSS-Fuzz-gen harness generation. This may take a long time''')
    start = time.time()
    
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
    log(f"Completed in {end-start} seconds")
    log(f"Your generated harnesses can be found in {project}-{project}..." +
                "as XX.fuzz_target. To use them, you can move them to your main folder and rename them.")

    os.chdir(main.OSS_FUZZ_GEN_DIR)
    subprocess.run(["python","-m", "report.web", "-r", WORK_DIR, "-o", REPORT_DIR])
    log(f"Report Generated in {REPORT_DIR}")
    log('''To view the report, either open up the index.html in your web browser or run the command:
    python -m http.server <port> -d <output-dir>''')

def consolidate_harnesses():
    None