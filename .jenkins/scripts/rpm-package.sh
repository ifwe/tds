#!/bin/bash


FPM_INTERPRETER=`echo "$interpreter" | sed -r 's/[0-9]/\0\./'`
FPM_PYPREFIX=$interpreter
FPM_CMD_PYTHON=python

FPM_PYPKG_VERSION=`$FPM_INTERPRETER setup.py --version | xargs $FPM_CMD_PYTHON -c "import sys; v = sys.argv[1]; print v.split('-', 1)[0] if '-' in v else v"`
FPM_PYPKG_ITERATION=`$FPM_INTERPRETER setup.py --version | xargs $FPM_CMD_PYTHON -c "import sys, string; v = sys.argv[1]; print '0.' + v.split('-', 1)[1] if '-' in v and v.split('-', 1)[1][0] not in string.digits else '1'"`

if [ "$os" == "centos65" ]; then
    FPM_ITERATION="$FPM_PYPKG_ITERATION.tagged.el6"
else
    FPM_ITERATION="$FPM_PYPKG_ITERATION.tagged.el7"
fi

if [ -n "$rvm_path" -a -f $rvm_path/scripts/rvm ]; then
    source $rvm_path/scripts/rvm
    rvm use system
fi

set -x

/usr/bin/fpm --verbose -s python -t rpm --rpm-auto-add-directories --python-bin $FPM_INTERPRETER --python-package-name-prefix $FPM_PYPREFIX_PREFIX$FPM_PYPREFIX --version $FPM_PYPKG_VERSION --iteration $FPM_ITERATION .

/usr/bin/fpm --verbose -s dir -t rpm -C ./etc --prefix /etc/init.d --name tds-update-yum-repo --template-scripts --template-value update_init=update_deploy_repo --after-install pkg/rpm/after_install.sh --before-remove pkg/rpm/before_remove.sh --depends "$FPM_PYPREFIX_PREFIX$FPM_PYPREFIX-tds = $FPM_PYPKG_VERSION-$FPM_ITERATION" --description 'Daemon to update repository for deployment application' --version $FPM_PYPKG_VERSION --iteration $FPM_ITERATION $FPM_EXTRAS .
