# Command loop breakdown/explanation
We will be looking at running oss-fuzz-gen's run-project.sh, running on a single project, shown as `<project>`. This may skip over some significant but less interesting functions/commands for brevity. This mainly serves as a guide to understand the flow of oss-fuzz, rather than how everything is done in oss-fuzz.
## How does oss-fuzz-gen run-project.sh work?
### Declaration of variables
These can be modified to change various program behaviors
```
OSS_FUZZ_GEN_DIR=$PWD
OSS_FUZZ_GEN_MODEL=${MODEL}
OSS_FUZZ_DIR=$OSS_FUZZ_GEN_DIR/work/oss-fuzz
FI_DIR=$OSS_FUZZ_GEN_DIR/work/fuzz-introspector
BENCHMARK_HEURISTICS=far-reach-low-coverage,low-cov-with-fuzz-keyword,easy-params-far-reach
VAR_HARNESSES_PER_PROJECT=4
PROJECTS=${@}
```
### Create a list of comma separated projects (not shown) and create an introspector report, webserver DB, and launch webserver
```
work/fuzz-introspector/oss_fuzz_integration/runner.py introspector <project> 1 --disable-webserver
python work/fuzz-introspector/tools/web-fuzzing-introspection/app/static/assets/db/web_db_creator_from_summary.py --local-oss-fuzz work/oss-fuzz
curl --silent http://localhost:8080/api/shutdown || true

FUZZ_INTROSPECTOR_LOCAL_OSS_FUZZ=work/oss-fuzz python3 work/fuzz-introspector/tools/web-fuzzing-introspection/app/main.py >> dev/null &
```
### Run run_all_experiments on the project
```
LLM_NUM_EVA=4 LLM_NUM_EXP=4 ./run_all_experiments.py --model=gpt-5 -g far-reach-low-coverage,low-cov-with-fuzz-keyword,easy-params-far-reach -gp <project> -gm 4 -of work/oss-fuzz -e http://127.0.0.1:8080/api
```
## How does run_all_experiments.py work?
### Short params table on oss-fuzz-gen, with the passed params from run-project.sh
|short | long | default | description | passed param |
| --- | --- | --- | --- | --- |
|-n | --num-samples | NUM_=2 | samples from LLM |  |
|-t | --temperature | TEMPERATURE=0.4 | 0 to 1 |  |
|-tr | --temperature-list | [ ] | list of temperatures  | |
|-c | --cloud-experiment-name | "" | cloud experiment name |  |
|-db | --cloud-experiment-bucket | "" | gcloud bucket |  |
|-b | --benchmarks-directory |  | benchmark directory |  |
|-y | --benchmark-yaml |  | benchmark yaml |  |
|-to | --run-timeout | RUN_TIMEOUT=30 | run timeout |  |
|-a | --ai-binary | "" | ai binary |  |
|-l |  --model | models.DefaultModel .name | model name | gpt-5 |
|-td | --template-directory | prompt_builder. DEFAULT _TEMPLATE_DIR | template-directory |  |
|-w | --work-dir | RESULTS_DIR= './results' |  |  |
|    | --context | False | add context to tested function | |
|-e | --introspector-endpoint | introspector .DEFAULT_INTROSPECTOR_ENDPOINT |  | http://127.0.0.1 :8080/api |
|-lo | --log-level | "info" |  | |
|-of | --oss-fuzz-dir | "" |  | work/oss-fuzz |
|-g | --generate-benchmarks |  |  | far-reach-low-coverage,low-cov-with-fuzz-keyword,easy-params-far-reach |
|-gp | --generate-benchmarks-projects |  |  | jupyter_server |
|-gm | --generate-benchmarks-max | 5 |  | 4 |
|    | --delay | 0 |  | |
|-p | --prompt-builder | "DEFAULT" |  | |
|-ag | --agent | False |  | |
|    | --custome-pipeline | False |  | |
|-mr | --max-round | 100 |  | |

### Report Generation
Starts the report with the start time and number of samples. add_to_json_report simply adds a key/value pair to a JSON report in the output directory with the name JSON_REPORT="report.json". It seems potentially inefficient as it loads a json report only to append to and overwrite it - O(n^2)
```
add_to_json_report(outdir: ./results, key: 'start_time', value: time.strftime(TIME_STAMP_FMT, time.gmtime(start)))
add_to_json_report(outdir: ./results, key: 'num_samples', value: 1)
```
### Introspector API Endpoint setup
Effectively just sets up all of the API endpoint variables within the introspector - e.g. `INTROSPECTOR_CFG = f'{endpoint}/annotated-cfg'".
```
introspector.set_introspector_endpoints(endpoint: introspector.DEFAULT_INTROSPECTOR_ENDPOINT = 'https://introspector.oss-fuzz.com/api')
```
### Cloning oss-fuzz to work/oss-fuzz
This step clones the oss-fuzz repository if it does not exist and syncs oss-fuzz data (not fully sure how this step really works). It then prepares the oss-fuzz directory for experiments by adding a glcoudignore, sets up a venv environment, and installs oss-fuzz requirements.
```
run_one_experiment.prepare(oss-fuzz-dir: 'work/oss-fuzz')\
    ->
    oss_fuzz_checkout.clone_oss_fuzz(oss_fuzz_dir: oss-fuzz-dir)
    oss_fuzz_checkout.postprocess_oss_fuzz()
    <-
```
### Benchmark Creation and Caching
This step creates a list of experiment targets based on a provided benchmark yaml. If a benchmark yaml was not provided, the introspector will generate benchmarks based on heuristics provided `--generate-benchmarks`. If `--generate-benchmarks` is also blank, it'll try to use project yamls specified in `--benchmarks-directory`. These project yamls are then converted into experiment classes and returned in an iterable list. If caching is enabled (set via environment variable `ENABLE_CACHING={0,1}`), docker images will be cached if there is a post-build script.
```
experiment_targets = prepare_experiment_targets(args) // -> experiment_configs == list[benchmarklib.Benchmark]
    ->
    if args.benchmark_yaml:
    // just uses specified benchmark yaml
    else:
        if args.generate_benchmarks:
            generate_benchmarks(args: args) // sets args.benchmarks_directory to point to new benchmarks
                ->
                project_lang = oss_fuzz_checkout.get_project_language(project)
                benchmarks = introspector.populate_benchmarks_using_introspector(project, project_lang, args.generate_benchmarks_max, benchmark_oracles)
                benchmarklib.Benchmark.to_yaml(benchmarks, outdir=benchmark_dir)
                <-
        // uses whatever yamls are in args.benchmarks_directory
    experiment_configs = []
    for benchmark_file in benchmark_yamls:
        experiment_configs.extend(benchmarklib.Benchmark.from_yaml(benchmark_file))
    <- 
if oss_fuzz_checkout.ENABLE_CACHING:
    oss_fuzz_checkout.prepare_cached_images(experiment_targets)
```
### Continous Coverage Analysis
This spins up a process that tries to process total gains from all generated harnesses for each project to update the JSON summary report every 5 minutes. Essentially, this allows per-project stats to be viewed as they are completed. 
```
coverage_gains_process = Process(target=extend_report_with_coverage_gains_process)
    -> extend_report_with_coverage_gains_process()
        -> extend_report_with_coverage_gains()
            coverage_gain_dict = _process_total_coverage_gain()
            existing_oss_fuzz_cov = introspector.query_introspector_language_stats()
            ... // Converts output of _process_total_coverage_gain() to a json file, with some processing
        <-
    <-
coverage_gains_process.start()
```
The `_process_total_coverage_gain()` function seems to be where the program attempts to load coverage from output files. When generating the coverage report dict, if there is an invalid coverage report (`max(total_cov.total_lines, total_existing_lines) == 0`), the warning messae "Line coverage information missing from the coverage report." is logged
```
textcov_dict: dict[str, list[textcov.Textcov]] = {}
for benchmark_dir in os.listdir(WORK_DIR):
    benchmark_used = benchmarklib.Benchmark.from_yaml(os.path.join(os.path.join(WORK_DIR, benchmark_dir, 'benchmark.yaml')))
    project_name = benchmark_used[0].project
    for sample in os.listdir(os.path.join(WORK_DIR, benchmark_dir, 'code-coverage-reports'))
        summary = os.path.join(WORK_DIR, benchmark_dir, 'code-coverage-reports', sample, 'textcov')
        for textcov_file in os.listdir(summary):
            // Adds a bunch of textcov.Textcov objects - `*.covreport` files, an `all_cov.json`, and a `jacoco.xml`
            textcov_dict[project_name].append(...)
coverage_gain: dict[str, dict[str, Any]] = {}
for project, cov_list in textcov_dict.items():
    existing_textcov = evaluator.load_existing_textcov(project)
    coverage_summary = evaluator.load_existing_coverage_summary(project)
    ... // Basically just does a bunch of loading and math
    coverate_gain[project] = {
          'language' : oss_fuzz_checkout.get_project_language(project),
          'coverage_diff' : total_cov.covered_lines / total_lines,
          'coverage_relative_gain' : cov_relative_gain,
          'coverage_ofg_total_covered_lines' : total_cov_covered_lines_before_subtraction,
          'coverage_ofg_total_new_covered_lines' : total_cov.covered_lines,
          'coverage_existing_total_covered_lines' : existing_textcov.covered_lines,
          'coverage_existing_total_lines' : total_existing_lines,
    }
return coverage_gain    
```
### Running experiments
This effectively just sets up a model and calls the experiment execution file, `run_one_experiment`
```
for target_benchmark in experiment_targets:
    result = run_experiments(benchmark: target_benchmark, args)
        ->
        model = models.LLM.setup(
            ai_binary=args.ai_binary,
            name=args.model,
            max_tokens=MAX_TOKENS,
            num_samples=args.num_samples,
            temperature=args.temperature,
            temperature_list=args.temperature_list,
        )
        result = run_one_experiment.run(benchmark=benchmark,
                                        model=model,
                                        args=args,
                                        work_dirs=args.work_dirs)
        <-
    _print_experiment_result(result)
    experiment_results.append(result)
```

### Final Coverage Aggregation
Kills the continous coverage process and generates a final coverage report, and prints out the experiment and coverage results.
```
if coverage_gains_process:
    coverage_gains_process.kill()
    extend_report_with_coverage_gains()

end = time.time()
add_to_json_report(args.work_dir, 'completion_time', time.strftime(TIME_STAMP_FMT, time.gmtime(end)))
add_to_json_report(args.work_dir, 'total_run_time', str(timedelta(seconds=end - start)))
coverage_gain_dict = _process_total_coverage_gain()
_print_experiment_results(experiment_results, coverage_gain_dict)
```
## How does run_one_experiment.py work?
run_one_experiment.py is a helper file that is not meant to be called by the CLI. 
