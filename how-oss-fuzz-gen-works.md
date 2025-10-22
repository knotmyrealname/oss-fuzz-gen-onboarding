# Command loop breakdown/explanation
We will be looking at running oss-fuzz-gen's run-project.sh, running on a single project, shown as `<project>`. This may skip over some significant but not interesting functions/commands for brevity.
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
introspector.set_introspector_endpoints(endpoint: introspector.DEFAULT_INTROSPECTOR_ENDPOINT = 'https://introspector.oss-fuzz.com/api')
### Cloning oss-fuzz to work/oss-fuzz
This step clones the oss-fuzz repository if it does not exist and syncs oss-fuzz data (not fully sure how this step really works). It then prepares the oss-fuzz directory for experiments by adding a glcoudignore, sets up a venv environment, and installs oss-fuzz requirements.
```
run_one_experiment.prepare(oss-fuzz-dir: 'work/oss-fuzz')\
    ->
    oss_fuzz_checkout.clone_oss_fuzz(oss_fuzz_dir: oss-fuzz-dir)
    oss_fuzz_checkout.postprocess_oss_fuzz()
    <-
```
### 
This step creates a list of experiment targets based on a provided benchmark yaml. If a benchmark yaml was not provided, the introspector will generate benchmarks based on heuristics provided `--generate-benchmarks`. If `--generate-benchmarks` is also blank, it'll try to use project yamls specified in `--benchmarks-directory`.  
```
experiment_targets = prepare_experiment_targets(args) // -> list[benchmarklib.Benchmark]
    ->
    if args.benchmark_yaml:
    ...
    else:
        if args.generate_benchmarks:
            generate_benchmarks(args: args)
                ->
                project_lang = oss_fuzz_checkout.get_project_language(project)
                benchmarks = introspector.populate_benchmarks_using_introspector(project, project_lang, args.generate_benchmarks_max, benchmark_oracles)
                benchmarklib.Benchmark.to_yaml(benchmarks, outdir=benchmark_dir)
                <-
    experiment_configs = []
    for benchmark_file in benchmark_yamls:
        experiment_configs.extend(benchmarklib.Benchmark.from_yaml(benchmark_file))
    <-
if oss_fuzz_checkout.ENABLE_CACHING:
    oss_fuzz_checkout.prepare_cached_images(experiment_targets)
```
