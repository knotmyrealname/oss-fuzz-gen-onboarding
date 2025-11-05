# An Easy way to get Started with Fuzzing
This collection of scripts serves as an entry into fuzzing with OSS-Fuzz, simplifying the whole process into one command line argument. We utilize existing functionality within OSS-Fuzz and OSS-Fuzz gen to make this happen to maximize compatibility, with some custom code to enable automatic corpus generation.

## Usage
Check out our detailed [usage guide](./USAGE.md) for documentation on available commands

## Setup
### Installation




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

## Helpful Resources

## Contact

## License