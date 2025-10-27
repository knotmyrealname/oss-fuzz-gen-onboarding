#!/usr/bin/env python3
import argparse
import sys
from commands import a, b

def main():
    parser = argparse.ArgumentParser(prog='ofgo', description='Onboard project into OSS-Fuzz-Gen.')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    a_parser = subparsers.add_parser("a", help="a")
    a_parser.add_argument("--aarg", type=str, default="all", help="a arg")
    b_parser = subparsers.add_parser("b", help="b")
    b_parser.add_argument("--barg", type=str, default="all", help="b arg")
    args = parser.parse_args()
    if args.command == 'a':
        a.run(args)
    elif args.command == 'b':
        b.run(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
