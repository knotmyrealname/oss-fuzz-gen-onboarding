# An Easy way to get Started with Fuzzing
This collection of scripts serves as an entry into fuzzing with OSS-Fuzz, simplifying the whole process into one command line argument. We utilize existing functionality within OSS-Fuzz and OSS-Fuzz gen to make this happen to maximize compatibility, with some custom code to enable automatic corpus generation. Note that, although we will be generating fuzzing harnesses, you will still have to **manually** add them to OSS-Fuzz via a pull request.

**NOTE: From our testing, OSS-Fuzz and OSS-Fuzz-gen DOES NOT work with Windows, and the same will be true for OFGO. This entire stack is designed for Linux - any support for other operating systems will be purely coincidental.**

## What is Fuzzing? 
At a high level, fuzzing is an automated software testing technique that runs programs with a large amount of mutated and randomly generated data to attempt to induce a fail condition/crash (which may lead to a bug/security vulnerability). 

## What is OSS-Fuzz?
OSS-Fuzz is a project created by Google for continuously fuzzing open source software. They accept projects through Github pull requests ([docs](https://google.github.io/oss-fuzz/getting-started/accepting-new-projects/)), where they initially expect only a project.yaml (created in oss-fuzz/projects/{your-project}). Before a project is submitted to OSS-Fuzz, it must be shown that it either has a significant user base or is critical to the global IT infrastructure (you can do this in your pull request - check pull request history to see examples). When a project is submitted, Google will run OSS-Fuzz on it every few days, with build logs provided on [this website](https://oss-fuzz-build-logs.storage.googleapis.com/index.html).

## What is OSS-Fuzz-gen?
TODO

## Setup
### Docker
OSS-Fuzz uses docker images to build and run fuzzers. Installation instructions for various Linux distributions may be found on the [Docker website](https://docs.docker.com/engine/install/)

### Installation
These installation instructions assume that python is installed and on path (with the exception of conda).

1. **Clone the Necessary Repositories** into the desired directory
```
## PUT UPDATED LINK
cd XXX
git submodule update --init --recursive
```
2. **Set up Python Environment** - This step is not strictly necessary, but highly recommended to maintain a clean working environment. From our testing, python 3.11 is required to run OSS-Fuzz and OSS-Fuzz-gen. 

 - **With Conda**
   - [Conda Installation for Linux](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html)
   - Setup: `conda create -n {name} python=3.11`
     - Replace {name} with the name of your conda environment
   - Activation: `conda activate {name}`
   - Deactivation: `conda deactivate`
 - **With venv**
   - Venv Installation: `pip install virtualenv`
   - Setup: `python3.11 -m venv venv`
   - Activation: `source venv/bin/activate`
   - Deactivation: `deactivate`

3. **Install Necessary Dependencies** - Make sure to do this while the `conda` or `venv` environment is activated

```
pip install -r requirements.txt
pip install -r oss-fuzz-gen/requirements.txt
```

## Usage
Check out our detailed [usage guide](./USAGE.md) for documentation on available commands

## Understanding Output
TODO

### Enabling GPT-5 Support
By default, OSS-Fuzz-gen does not support OpenAI's GPT-5 models. If you would like to work with GPT-5, we have provided a fork with a patch to enable GPT-5. Note that GPT-5 will only work with a temperature of 1 (set by `--temperature 1`). To enable this patch, run the following commands:

```
git submodule set-url -- oss-fuzz-gen https://github.com/knotmyrealname/oss-fuzz-gen
git submodule update --remote --recursive
```
Note that this may not be up-to-date with the latest version of OSS-Fuzz-gen. If this is the case, feel free to open up an issue and we will attempt to update the fork as soon as possible. 

Currently, the following GPT-5 models are supported:
 - gpt-5
 - gpt-5-mini
 - gpt-5-nano

## Contact
For questions, comments, or support, please create a Github issue. A contributor will respond whenever they are available

TODO - create issue template
