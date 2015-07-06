#!/bin/bash

echo '#!/bin/bash

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
' > rpm-package.sh

chmod +x rpm-package.sh

echo 'FROM dockerregistry.tagged.com/siteops/centos:6.5
MAINTAINER Ken Lareau <klareau@ifwe.co>

RUN /usr/bin/yum-config-manager --add-repo http://serverbuild.tagged.com/deploy
RUN /usr/bin/yum-config-manager --add-repo http://serverbuild.tagged.com/tagrepo/CentOS/6
RUN /usr/bin/yum-config-manager --add-repo http://serverbuild.tagged.com/tagged-updates/CentOS/6.5
RUN /usr/bin/yum-config-manager --add-repo http://serverbuild.tagged.com/CentOS6.5/epel/x86_64
RUN /usr/bin/yum-config-manager --add-repo http://serverbuild.tagged.com/CentOS6.5/updates/x86_64
RUN /usr/bin/yum-config-manager --add-repo http://serverbuild.tagged.com/CentOS6.5/os/x86_64
RUN /usr/bin/yum-config-manager --add-repo http://serverbuild.tagged.com/CentOS6.2/ius/x86_64
RUN /usr/bin/yum makecache

RUN yum -y --nogpgcheck update
RUN yum -y --nogpgcheck install sudo
RUN yum -y --nogpgcheck install gcc
RUN yum -y --nogpgcheck install git
RUN yum -y --nogpgcheck install python27
RUN yum -y --nogpgcheck install python-devel
RUN yum -y --nogpgcheck install python-pip
RUN yum -y --nogpgcheck install python27-setuptools
RUN yum -y --nogpgcheck install expat-devel
RUN yum -y --nogpgcheck install openssl-devel
RUN yum -y --nogpgcheck install rubygems
RUN yum -y --nogpgcheck install rubygem-fpm
RUN yum -y --nogpgcheck install rpm-build

RUN mkdir -p /opt/python
COPY . /opt/python
WORKDIR /opt/python

ENV interpreter python27
ENV GEM_HOME /usr/lib/ruby/gems/1.8/gems
ENV os centos65
ENV FPM_COMMAND_PATH /usr/bin
' > Dockerfile.centos65

docker pull dockerregistry.tagged.com/siteops/centos:6.5
docker build -t python-centos-65 -f Dockerfile.centos65 .
docker run --name=python-centos-65 python-centos-65 ./rpm-package.sh
docker cp python-centos-65:/opt/python/.rpm .
docker rm python-centos-65
docker rmi python-centos-65

echo 'FROM dockerregistry.tagged.com/siteops/centos:7.1
MAINTAINER Ken Lareau <klarea@ifwe.co>

RUN /usr/bin/yum-config-manager --add-repo http://serverbuild.tagged.com/deploy
RUN /usr/bin/yum-config-manager --add-repo http://serverbuild.tagged.com/tagrepo/CentOS/7
RUN /usr/bin/yum-config-manager --add-repo http://serverbuild.tagged.com/tagged-updates/CentOS/7.1
RUN /usr/bin/yum-config-manager --add-repo http://serverbuild.tagged.com/CentOS7.1/epel/x86_64
RUN /usr/bin/yum-config-manager --add-repo http://serverbuild.tagged.com/CentOS7.1/updates/x86_64
RUN /usr/bin/yum-config-manager --add-repo http://serverbuild.tagged.com/CentOS7.1/os/x86_64
RUN /usr/bin/yum makecache

RUN yum -y --nogpgcheck update
RUN yum -y --nogpgcheck install sudo
RUN yum -y --nogpgcheck install gcc
RUN yum -y --nogpgcheck install git
RUN yum -y --nogpgcheck install python-devel
RUN yum -y --nogpgcheck install python-pip
RUN yum -y --nogpgcheck install python-setuptools
RUN yum -y --nogpgcheck install expat-devel
RUN yum -y --nogpgcheck install openssl-devel
RUN yum -y --nogpgcheck install rubygems
RUN yum -y --nogpgcheck install rubygem-fpm
RUN yum -y --nogpgcheck install rpm-build

RUN mkdir -p /opt/python
COPY . /opt/python
WORKDIR /opt/python

ENV interpreter python
ENV GEM_HOME /usr/local/share/gems/gems
ENV os centos71
ENV FPM_COMMAND_PATH /usr/local/share/gems/gems/bin
' > Dockerfile.centos71

docker pull dockerregistry.tagged.com/siteops/centos:7.1
docker build -t python-centos-71 -f Dockerfile.centos71 .
docker run --name=python-centos-71 python-centos-71 ./rpm-package.sh
docker cp python-centos-71:/opt/python/.rpm .
docker rm python-centos-71
docker rmi python-centos-71
