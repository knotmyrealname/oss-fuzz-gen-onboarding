import sys
import os
import logging
import time
import subprocess

sys.path.insert(0, "./work/oss-fuzz-gen")
import run_all_experiments

## Variable declaration
BASE_DIR = os.path.dirname(__file__)
BENCHMARK_HEURISTICS = "far-reach-low-coverage,low-cov-with-fuzz-keyword,easy-params-far-reach"
NUMBER_OF_HARNESSES = 1
OSS_FUZZ_DIR = os.path.join(BASE_DIR, "work/oss-fuzz")
WORK_DIR = os.path.join(BASE_DIR, "results")


## new stuff
OSS_FUZZ_GEN_DIR = os.path.join(BASE_DIR, "work/oss-fuzz-gen")
REPORT_DIR = os.path.join(BASE_DIR, "report")

os.chdir(OSS_FUZZ_GEN_DIR)
subprocess.run(["python","-m", "report.web", "-r", WORK_DIR, "-o", REPORT_DIR])