#!/bin/bash

VERSION=`cat version.py | grep __version__ | awk '{print $3}' | sed "s/'//g"`

docker pull dockerregistry.tagged.com/siteops/centos:6.5
docker build -t tds-centos-65 -f Dockerfile.centos65 .
docker run --name=tds-centos-65 tds-centos-65 ./.jenkins/scripts/rpm-package.sh
docker cp tds-centos-65:/opt/deploy/tds-update-yum-repo-$VERSION-1.tagged.el6.x86_64.rpm .
docker cp tds-centos-65:/opt/deploy/python27-tds-$VERSION-1.tagged.el6.noarch.rpm .
docker rm tds-centos-65
docker rmi tds-centos-65

docker pull dockerregistry.tagged.com/siteops/centos:7.1
docker build -t tds-centos-71 -f Dockerfile.centos71 .
docker run --name=tds-centos-71 tds-centos-71 ./.jenkins/scripts/rpm-package.sh
docker cp tds-centos-71:/opt/deploy/tds-update-yum-repo-$VERSION-1.tagged.el7.x86_64.rpm .
docker cp tds-centos-71:/opt/deploy/python-tds-$VERSION-1.tagged.el7.noarch.rpm .
docker rm tds-centos-71
docker rmi tds-centos-71
