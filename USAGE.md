# In order to populate the submodules run the following:
```
git submodule set-url -- oss-fuzz-gen \
https://github.com/knotmyrealname/oss-fuzz-gen

git submodule set-url -- oss-fuzz \
https://github.com/google/oss-fuzz.git

git submodule update --init --recursive
```

# To setup the environment to run this project do the following.
# Create virtual environment
```python3.11 -m venv venv```

# Activate virtual environment
# On Linux/macOS:
```source venv/bin/activate```
# On Windows:
```venv\Scripts\activate```

# Upgrade pip
```pip install --upgrade pip```

# Install dependencies
```pip install -r oss-fuzz-gen/requirements.txt```

# Set environment variables for open-ai api key
```export OPENAI_API_KEY="your-api-key-here"``` 

# For new projects that need complete setup
```
python3 oss_fuzz_gen_onboarding.py default \
  --repo <REPO_URL> \
  --email <MAINTAINER_EMAIL> \
  [--model gpt-5] \
  [--temperature 1] 
  ``` 

# Creating new harnesses for existing projects
```
python3 oss_fuzz_gen_onboarding.py pre-existing \
  --project <PROJECT_NAME> \
  [--model gpt-5] \
  [--temperature 1]
```

# Only generating coverage reports for existing projects
```
python3 oss_fuzz_gen_onboarding.py pre-existing \
  --project <PROJECT_NAME>
```

# Creating new seed corpuses using LLMs
```
python3 oss_fuzz_gen_onboarding.py corpus-gen \
  --project <PROJECT_NAME> \
  [--model gpt-5] \
  [--temperature 1]
```