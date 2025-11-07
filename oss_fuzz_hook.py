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

"""
OSS-Fuzz Runner
Will run existing or newly generated OSS-Fuzz harnesses
"""
import os
import subprocess

import oss_fuzz_gen_onboarding as main
from logger_config import setup_logger

BASE_DIR = os.path.dirname(__file__)

logger = setup_logger(__name__)

## Purple
def log(output):
    logger.info(f"\033[95moss_fuzz_hook:\033[00m {output}")

"""
Create build images and fuzz the specified project with oss-fuzz
using infra/helper.py.
"""
def run_project(project: str = None):
    path_to_helper = os.path.join(main.OSS_FUZZ_DIR, "infra", "helper.py")
    log(f"Running {project} with OSS-FUZZ.")
    commands = [
        ["python3", path_to_helper, "pull_images"],
        ["python3", path_to_helper, "build_image", project],
        ["python3", path_to_helper, "build_fuzzers", project]
    ]
    for c in commands:
        log(f"Building images for {project}")
        if c == ["python3", path_to_helper, "build_image", project]:
            res = subprocess.run(c, input="y\n", text=True)
        else:
            res = subprocess.run(c)
        if res.returncode != 0:
            log(f"Error: {res.stderr}")
            break
        else:
            log(f"Success: f{c}")
    
    path_to_fuzzers = os.path.join(main.OSS_FUZZ_DIR, "build", "out", project)
    #Finding the fuzzers to run
    if not os.path.exists(path_to_fuzzers):
        log(f"Fuzzers directory not found: {path_to_fuzzers}")
        return False
    
    fuzz_name = ""
    for i in os.listdir(path_to_fuzzers):
        if(i.startswith("fuzz_") and '.' not in i):
            fuzz_name = i
            break
    if fuzz_name is None:
        log("Error: No fuzzer found.")
        return False
    log(f"Running {fuzz_name}.")
    subprocess.run(["python3", path_to_helper, "run_fuzzer", project, fuzz_name,"--", "-max_total_time=10", "-runs=1000"])
