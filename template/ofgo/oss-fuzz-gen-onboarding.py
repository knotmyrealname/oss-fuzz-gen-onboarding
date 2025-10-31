#!/usr/bin/env python3
import argparse
import sys
import re
from urllib.parse import urlparse
import shlex
from email_validator import validate_email, EmailNotValidError
from commands import a, b

DEFAULT_CMD = 'a'
KNOWN_COMMANDS = {'a', 'b', 'full', 'h'}

def check_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not bool(re.fullmatch(regex, email)):
        raise ValueError(f'Invalid email address {email}')
    try:
        valid_email = validate_email(email)
        return valid_email.email
    except EmailNotValidError as e:
        raise ValueError(f"Invalid email: {email}") from e

def check_url(url):
    regex = re.compile(r'https?://[^\s/$.?#].[^\s]*')
    if not bool(regex.fullmatch(url)):
        raise ValueError(f'Invalid repo URL {url}')
    parsed = urlparse(url)
    if parsed.scheme != 'https':
        raise ValueError(f'URL {url} not HTTPS')
    if not parsed.netloc.endswith('github.com') and not parsed.netloc.endswith('gitlab.com'):
        raise ValueError(f'URL {url} not GitHub or GitLab')
    return shlex.quote(url)

def build_parser():
    parser = argparse.ArgumentParser(
        prog='ofgo',
        description='Onboard project into OSS-Fuzz-Gen',
        add_help=False
    )

    # Global -h/--help flag
    parser.add_argument('-h', '--help', action='store_true', help='Show this help message and exit')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # full command example
    full = subparsers.add_parser('full', help='Full onboarding with harness and corpii generation')
    full.add_argument('--repo', type=str, help='Project repo URL')
    full.add_argument('--email', type=str, help='Project maintainer email')

    # command a
    a_p = subparsers.add_parser('a', help='Run command a')
    a_p.add_argument('--aarg', type=str, default='all', help='Argument for a')

    # command b
    b_p = subparsers.add_parser('b', help='Run command b')
    b_p.add_argument('--barg', type=str, default='all', help='Argument for b')

    return parser

def main():
    parser = build_parser()

    # Args after script name
    raw_argv = sys.argv[1:]

    # Handle help in args
    if '-h' in raw_argv or '--help' in raw_argv:
        parser.print_help()
        sys.exit(0)

    # No args default to full
    if not raw_argv:
        argv = ['full']
    else:
        # Use subcommand as-is
        if raw_argv[0] in KNOWN_COMMANDS:
            argv = raw_argv
        # Inject default for args
        else:
            argv = ['full'] + raw_argv

    # Parse arguments
    args = parser.parse_args(argv)

    # Dispatch
    if args.command == 'a':
        a.run(args)
    elif args.command == 'b':
        b.run(args)
    elif args.command == 'full':
        try:
            if not args.repo or not args.email:
                raise ValueError('Missing arguments --repo and --email for full onboarding')
            email = check_email(args.email)
            repo = check_url(args.repo)
        except ValueError as ve:
            print(f'Error: {ve}')
            sys.exit(1)
        print(f'Running full onboarding for repo: {repo}, maintainer: {email}')
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()