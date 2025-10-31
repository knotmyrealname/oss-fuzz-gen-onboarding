import shlex
import sys
import os
import logging
from openai import OpenAI

import harness_gen
import oss_fuzz_hook

BASE_DIR = os.path.dirname(__file__)
DEFAULT_MODEL = "gpt-5"

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

def run_interactive():
    ##TODO
    print("interactive")

def run_noninteractive(args):
    ##TODO
    print(f"noninteractive {repo_url} {email}")   

def run_harnessgen(args):
    harness_gen.generate_harness(args.model, args.project, args.temperature)
    print(f"harnessgen {project}")

def run_ossfuzz(args):
    oss_fuzz_hook.run_project(project)
    print(f"ossfuzz {project}")

def run_corpusgen(args):
    ##TODO
    print(f"corpusgen {project}")

def project_exists(args):
    project_location = os.path.join(BASE_DIR, f"work/oss-fuzz/projects/{project}")
    return os.path.exists(project_location)


## Note that this will use a small amount of API credits
def model_valid(model, temperature):
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    try:
        response = client.responses.create(model=model, 
                                           input="test", 
                                           max_output_tokens=5,
                                           temperature=temperature)
    except:
        return False
    return True

def run_on_args():
    parser = argparse.ArgumentParser(
        prog='ofgo',
        description='Onboard project into OSS-Fuzz-Gen',
        #add_help=False
    )

    # Global -h/--help flag
    #parser.add_argument('-h', '--help', action='store_true', help='Show this help message and exit')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Run the default
    ni = subparsers.add_parser('--default', help='Full onboarding with harness and corpii generation')
    ni.add_argument('-repo', type=str, help='Project repo URL')
    ni.add_argument('-email', type=str, help='Project maintainer email')
    ni.add_argument('-model', type=str, default="gpt-5", help="")
    ni.add_argument('-temperature', type=int, default=1, help="")
    ni.set_defaults(func=run_noninteractive)

    # Run only OSS-Fuzz-gen
    pe = subparsers.add_parser('--pre-existing', help='Run command a')
    pe.add_argument('-project', type=str, default='all', help='Argument for a')
    pe.add_argument('-model', type=str, default="gpt-5", help="")
    pe.add_argument('-temperature', type=int, default=1, help="")
    pe.set_defaults(func=run_harnessgen)

    # Run OSS-Fuzz
    cv = subparsers.add_parser('--coverage', help='Run command b')
    cv.add_argument('-project', type=str, default='all', help='Argument for b')
    cv.set_defaults(func=run_ossfuzz)

    # Run corpus generation
    cg = subparsers.add_parser('--corpus-gen', help='Run command a')
    cg.add_argument('-project', type=str, default='all', help='Argument for a')
    cg.add_argument('-model', type=str, default="gpt-5", help="")
    cg.add_argument('-temperature', type=int, default=1, help="")
    cg.set_defaults(func=run_corpusgen)

}

def main():
    if len(sys.argv) == 1:
        run_interactive()
    else{
        run_on_args()
    }    

if __name__ == "__main__":
    main()