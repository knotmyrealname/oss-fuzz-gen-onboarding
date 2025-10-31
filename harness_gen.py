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
NUM_SAMPLES = 1
OSS_FUZZ_DIR = os.path.join(BASE_DIR, "work/oss-fuzz")
WORK_DIR = os.path.join(BASE_DIR, "results")
OSS_FUZZ_GEN_DIR = os.path.join(BASE_DIR, "work/oss-fuzz-gen")
REPORT_DIR = os.path.join(BASE_DIR, "report")

logger = logging.getLogger(__name__)

def generate_harness(model : str, project : str, temperature : float = 0.4):
    logging.basicConfig(level=logging.INFO,
                       format=run_all_experiments.LOG_FMT,
                       datefmt='%Y-%m-%d %H:%M:%S')
    
    ## Checks to make sure project is valid (assumes model has already been checked by main method)
    project_location = os.path.join(BASE_DIR, "work/oss-fuzz/projects/{project}")
    if not os.path.exists(project_location):
        logger.info(f"Invalid Project ({project}) at {project_location}")

    logger.info(f'''\nBeginning OSS-Fuzz-gen harness generation
This may take a long time''')
    start = time.time()
    
    subprocess.run([os.path.join(BASE_DIR, "work/oss-fuzz-gen/run_all_experiments.py"),
                    f"--model={model}",
                    f"--generate-benchmarks={BENCHMARK_HEURISTICS}",
                    f"--generate-benchmarks-projects={project}",
                    f"--generate-benchmarks-max={NUMBER_OF_HARNESSES}",
                    f"--oss-fuzz-dir={OSS_FUZZ_DIR}",
                    f"--temperature={temperature}",
                    f"--work-dir={WORK_DIR}",
                    f"--num-samples={NUM_SAMPLES}"])

    end = time.time()
    logger.info(f"\033[96mharness_gen:\033[00m Completed in {end-start} seconds")
    logger.info(f"\033[96mharness_gen:\033[00m Your generated harnesses can be found in {project}-{project}..." +
                "as XX.fuzz_target. To use them, you can move them to your main folder and rename them.")

    os.chdir(OSS_FUZZ_GEN_DIR)
    subprocess.run(["python","-m", "report.web", "-r", WORK_DIR, "-o", REPORT_DIR])
    logger.info(f"\033[96mharness_gen:\033[00m Report Generated in {REPORT_DIR}")
    logger.info('''\033[96mharness_gen:\033[00m To view the report, either open up the index.html in your web browser or run the command:
    python -m http.server <port> -d <output-dir>''')
