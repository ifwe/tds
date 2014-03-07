#!/bin/bash

scripts=$( dirname "${BASH_SOURCE-$0}" )
source $scripts/python-setup.sh

for d in tds tests ; do
    pylint -f parseable -r n $d >> reports/pylint.log || :
    flake8 --max-complexity 8 $d >> reports/pyflakes.log || :
done
