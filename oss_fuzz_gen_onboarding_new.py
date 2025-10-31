import shlex
import sys
import os
import logging

import harness_gen
import oss_fuzz_hook

BASE_DIR = os.path.dirname(__file__)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(levelname)s - %(message)s',
                       datefmt='%Y-%m-%d %H:%M:%S')

def valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if bool(re.fullmatch(regex, email)):
        return True
    return False

def validate_repo(url) :
    regex = re.compile(r'https?://[^\s/$.?#].[^\s]*')
    if not bool(regex.fullmatch(url)):
        raise ValueError(f'Invalid repo URL {url}')
    parsed = urlparse(url)
    if not parsed.netloc.endswith('github.com') and not parsed.netloc.endswith('gitlab.com'):
        raise ValueError(f'URL {url} not GitHub or GitLab')
    if parsed.scheme != 'https':
        raise ValueError(f'URL {url} not HTTPS')
    return shlex.quote(url)

def valid_repo(url) :
    regex = re.compile(r'https?://[^\s/$.?#].[^\s]*')
    if not bool(regex.fullmatch(url)):
        return False
    parsed = urlparse(url)
    if parsed.scheme != 'https':
        return False
    if not parsed.netloc.endswith('github.com') and not parsed.netloc.endswith('gitlab.com'):
        return False
    return True

def run_interactive():
    ##TODO
    print("interactive")

def run_noninteractive(repo_url: str, email: str):
    ##TODO
    print(f"noninteractive {repo_url} {email}")   

def run_harnessgen(project: str):
    ##TODO
    print(f"harnessgen {project}")

def run_ossfuzz(project: str):
    ##TODO
    print(f"ossfuzz {project}")

def run_corpusgen(project: str):
    ##TODO
    print(f"corpusgen {project}")

def project_exists(project: str):
    project_location = os.path.join(BASE_DIR, f"work/oss-fuzz/projects/{project}")
    return os.path.exists(project_location)

def usage(info: str):
    print(f"Usage: {info}")

def main():
    args = sys.argv

    if len(args) == 1:
        run_interactive()
    elif args[1] == "--pre-existing":
        if len(args) == 3:
            if project_exists(args):
                run_harnessgen(project)
            else:
                usage("TODO")
        else:
            usage("TODO")
    elif args[1] == "--coverage":
        if len(args) == 3:
            if project_exists(args):
                run_ossfuzz(project)
            else:
                usage("TODO")
        else:
            usage("TODO")
    elif args[1] == "--corpus-gen":
        if len(args) == 3:
            if project_exists(args):
                run_corpusgen(project)
            else:
                usage("TODO")
        else:
            usage("TODO")
    else:
        if len(args) == 3:
            if valid_repo(args[2]):
                if valid_email(args[3]):
                    run_noninteractive(validate_repo,args[3])
                else:
                    usage("TODO")
            else:
                usage("TODO")
        else:
            usage("TODO")
        

if __name__ == "__main__":
    main()