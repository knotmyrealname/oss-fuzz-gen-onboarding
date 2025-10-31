#!/usr/bin/env python3
"""
OSS-Fuzz Runner
Will run existing or newly generated OSS-Fuzz harnesses
"""

import os, subprocess, logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OSSFuzzRunner:
    def __init__(self, oss_fuzz_dir: str = None):
        self.oss_fuzz_dir = oss_fuzz_dir

    """
    Create build images and fuzz the specified project with oss-fuzz
    using infra/helper.py.
    """
    def run_project(self, project: str = None):
        path_to_helper = os.path.join(self.oss_fuzz_dir, "infra", "helper.py")
        path_to_fuzzers = os.path.join(self.oss_fuzz_dir, "build", "out", project)
        commands = [
            ["python3", path_to_helper, "pull_images"],
            ["python3", path_to_helper, "build_image", project],
            ["python3", path_to_helper, "build_fuzzers", project]
        ]
        for c in commands:
            res = subprocess.run(c, capture_output=True)
            if res.returncode != 0:
                print(f"Error: {res.stderr}")
                break
            else:
                print(f"Success: f{c}")
        
        #Finding the fuzzers to run
        if not os.path.exists(path_to_fuzzers):
            print(f"Fuzzers directory not found: {path_to_fuzzers}")
            return False
        
        fuzz_name
        for i in os.listdir(path_to_fuzzers):
            if(i.startswith("fuzz_") and '.' not in i):
                fuzz_name = i
                print(f"Fuzzer found: {fuzz_name}")
                break
        if fuzz_name is None:
            print("Error: No fuzzer found.")
            return False
        
        subprocess.run(["python3", path_to_helper, "run_fuzzer", project, {fuzz_name},"--", "-max_total_time=60"])
        



        

        