#!/bin/bash

FPM_INTERPRETER=`echo "$interpreter" | sed -r "s/[0-9]/\0\./"`
FPM_PYPREFIX=$interpreter
FPM_PACKAGE_VERSION="latest"
FPM_PACKAGE_ITERATION=1
FPM_TAGGED_ITERATION=1

if [ "$FPM_PACKAGE_VERSION" == "latest" -o -z "$FPM_PACKAGE_VERSION" ]; then
    FPM_VERSION=""
else
    FPM_VERSION="--version $FPM_PACKAGE_VERSION"
fi

if [ "$os" == "centos65" ]; then
    FPM_ITERATION="$FPM_PYPKG_ITERATION.tagged.el6"
else
    FPM_ITERATION="$FPM_PYPKG_ITERATION.tagged.el7"
fi

if [ -n "$rvm_path" -a -f $rvm_path/scripts/rvm ]; then
    source $rvm_path/scripts/rvm
    rvm use system
fi
export GEM_HOME=/usr/lib/ruby/gems/1.8

set -x

echo "$FPM_COMMAND_PATH/fpm --verbose -s python -t rpm --rpm-auto-add-directories --python-bin $FPM_INTERPRETER --python-package-name-prefix $FPM_PYPREFIX_PREFIX$FPM_PYPREFIX $FPM_VERSION --iteration $FPM_ITERATION --vendor Tagged $(echo $(eval echo $FPM_EXTRAS)) $FPM_NAME"
$FPM_COMMAND_PATH/fpm --verbose -s python -t rpm --rpm-auto-add-directories --python-bin $FPM_INTERPRETER --python-package-name-prefix $FPM_PYPREFIX_PREFIX$FPM_PYPREFIX $FPM_VERSION --iteration $FPM_ITERATION --vendor Tagged $(echo $(eval echo $FPM_EXTRAS)) $FPM_NAME

