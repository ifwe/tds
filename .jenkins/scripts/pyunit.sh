#!/bin/bash

mkdir -p reports
rm reports/pyunit.xml

"$WORKSPACE/run_tests.py" \
    -v \
    --junitxml=reports/pyunit.xml \
    --cov-report=xml \
    --cov-config=coverage.rc \
    --cov=tds \
    --ignore="$VIRTUAL_ENV" ||:
