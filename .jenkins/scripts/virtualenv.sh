#!/bin/bash

export SITEOPS_VIRTUALENV=$WORKSPACE/jenkins-venv
export PYTHONPATH=$PYTHONPATH:.

if [ ! -z "$VIRTUAL_ENV" ] ; then
    source "$VIRTUAL_ENV/bin/activate"
    deactivate
fi

if ! [[ -d "$SITEOPS_VIRTUALENV" && -f "$SITEOPS_VIRTUALENV/bin/activate" ]] ; then
    if ! which virtualenv-2.7 ; then
        wget http://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.9.1.tar.gz
        tar -xzf virtualenv-1.9.1.tar.gz
        rm virtualenv-1.9.1.tar.gz
        pushd virtualenv-1.9.1
        python2.7 virtualenv.py "$SITEOPS_VIRTUALENV"
        popd
    else
        virtualenv-2.7 "$SITEOPS_VIRTUALENV"
    fi

    if [ -d virtualenv-1.9.1 ] ; then
        rm -rf virtualenv-1.9.1
    fi
fi

export PATH=$PATH:$SITEOPS_VIRTUALENV/bin
source "$SITEOPS_VIRTUALENV/bin/activate"
