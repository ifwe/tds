#!/bin/bash

mkdir -p reports
rm reports/pylint.log
rm reports/pyflakes.log

for d in tds tests ; do
    pylint --rcfile=.pylintrc -f parseable -r n --disable=similarities $d >> reports/pylint.log || :
    flake8 --max-complexity 8 $d >> reports/pyflakes.log || :
done
