#!/bin/bash

mkdir work
cd work
git clone https://github.com/knotmyrealname/oss-fuzz-gen.git
git clone https://github.com/google/oss-fuzz.git
git clone https://github.com/google/oss-fuzz-gen.git
cd oss-fuzz-gen
pip install -r oss-fuzz-gen/requirements.txt
cd ..
##TODO SET oss-fuzz-gen/work/oss-fuzz dir to point to the path pwd/oss-fuzz

## Installing in a virtual environment
#cd ..
#python3.11 -m venv venv
#source venv/bin/activate
#pip install --upgrade pip
#pip install -r work/oss-fuzz-gen/requirements.txt

