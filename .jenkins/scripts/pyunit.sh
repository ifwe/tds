#!/bin/bash

scripts=$( dirname "${BASH_SOURCE-$0}" )
source "$scripts/python-setup.sh"

"$WORKSPACE/run_tests.py" \
    -v \
    --junitxml=reports/pyunit.xml \
    --cov-report=xml \
    --cov=tds \
    --ignore="$VIRTUAL_ENV" ||:
