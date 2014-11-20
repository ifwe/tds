#!/bin/bash

if [[ -z "$WORKSPACE" ]] ; then
    scripts=$( dirname "${BASH_SOURCE-$0}" )
    scripts=$( cd "$scripts">/dev/null; pwd )
    export WORKSPACE=$( cd "$scripts/../.." >/dev/null; pwd )
fi

source $scripts/virtualenv.sh

if [ -f requirements-dev.txt ]; then
   pip install -r requirements-dev.txt --allow-all-external --allow-unverified progressbar
fi

if [ -f requirements.txt ]; then
   pip install -r requirements.txt --allow-all-external --allow-unverified progressbar
fi
