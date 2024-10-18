#!/bin/bash

set -e

if [ "$#" -lt 1 ] ; then
    cat >&2 <<EOF
usage: $0 [package]

available package names:
* python-tds
* tds-installer
* tds-update-yum-repo
EOF

    exit 1
fi

PACKAGE=$1

ITERATION=${PARENT_BUILD_NUMBER:-1}

declare -a COMMON_CMD=(\
    docker_build/run.sh \
    --iteration "$ITERATION" \
)

declare -a DAEMON_CMD=(\
    "${COMMON_CMD[@]}" \
    -s dir \
    --depends-same-version python-tds \
    --version-py \
    -- \
    -a noarch \
    --template-scripts \
    --after-install pkg/rpm/after_install.sh.erb \
    --before-remove pkg/rpm/before_remove.sh.erb \
    --after-remove pkg/rpm/after_remove.sh.erb \
    --no-rpm-auto-add-directories \
    --prefix /lib/systemd/system \
)


declare -a CMD
case "$PACKAGE" in
    python-tds )
        CMD=("${COMMON_CMD[@]}")
    ;;
    tds-installer )
        CMD=( \
            "${DAEMON_CMD[@]}" \
            -C systemd/tds_installer \
            --template-value unit=tds_installer.service \
            --name tds-installer \
            --description 'Daemon to manage installations for deployment application' \
        )
    ;;
    tds-update-yum-repo )
        CMD=( \
            "${DAEMON_CMD[@]}" \
            -C systemd/update_deploy_repo \
            --template-value unit=update_deploy_repo.service \
            --name tds-update-yum-repo \
            --description 'Daemon to update repository for deployment application' \
        )
    ;;
    * )
        echo "error: unrecognized package name: $PACKAGE" >&2
        exit 1
    ;;
esac

exec "${CMD[@]}"
