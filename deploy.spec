%define _topdir    %(pwd)
%define _tmppath   %{_topdir}
%define _builddir  %{_tmppath}
%define _buildrootdir %{_tmppath}

%define _rpmtopdir    %{_topdir}
%define _sourcedir    %{_rpmtopdir}
%define _specdir      %{_topdir}
%define _rpmdir       %{_topdir}
%define _srcrpmdir    %{_topdir}
%define _rpmfilename  %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm

%global manage_init  manage_deploy_rpms
%global update_init  update_deploy_repo

%if 0%{?rhel} >= 6
%global __python python
%global pybase %{__python}
%global tagbase TAGpython
%else
%global __python python2.6
%global pybase python26
%global tagbase TAGpython26
%endif

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           TAGpython-deploy
Version:        %(%{__python} setup.py --version)
Release:        1%{?dist}
Summary:        Manage deployment of Tagged applications

Group:          Applications/Python
License:        MIT
URL:            None
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  %{pybase}-devel

#Requires: %{tagbase}-tagopsdb
#Requires: %{tagbase}-argparse
#Requires: %{tagbase}-beanstalkc
#Requires: %{tagbase}-orderreddict


%description
Application to manage deployment of Tagged applications


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
# Note: use --install-scripts <path> for alternate location of programs
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/etc/init.d/
cp etc/%{manage_init} $RPM_BUILD_ROOT/etc/init.d/%{manage_init}
cp etc/%{update_init} $RPM_BUILD_ROOT/etc/init.d/%{update_init}
chmod +x $RPM_BUILD_ROOT/etc/init.d/%{manage_init}
chmod +x $RPM_BUILD_ROOT/etc/init.d/%{update_init}
 

%clean
%{__python} setup.py clean --all
rm -rf $RPM_BUILD_ROOT


%package copy-package
Summary: Copy package daemon for deployment
Group: Applications/Python

#Requires: %{tagbase}-tagopsdb
#Requires: %{tagbase}-beanstalkc
#Requires: %{tagbase}-daemonize

Requires(post): chkconfig
Requires(preun): chkconfig
Requires(preun): initscripts

%description copy-package
Daemon to manage copying of RPMs to repository for deployment application

%post copy-package
/sbin/chkconfig --add %{manage_init}

%preun copy-package
if [ $1 -eq 0 ] ; then
    /sbin/service %{manage_init} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{manage_init}
fi


%package update-repo
Summary: Update repository daemon for deployment
Group: Applications/Python

#Requires: %{tagbase}-tagopsdb
#Requires: %{tagbase}-beanstalkc
#Requires: %{tagbase}-daemonize

Requires(post): chkconfig
Requires(preun): chkconfig
Requires(preun): initscripts

%description update-repo
Daemon to update repository for deployment application

%post update-repo
/sbin/chkconfig --add %{update_init}

%preun update-repo
if [ $1 -eq 0 ] ; then
    /sbin/service %{update_init} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{update_init}
fi


%files
%defattr(-,root,root,-)
%doc
%{python_sitelib}/*
/usr/bin/tds

%files copy-package
%defattr(-,root,root,-)
%doc
/usr/bin/manage_deploy_rpms
/etc/init.d/%{manage_init}

%files update-repo
%defattr(-,root,root,-)
%doc
/usr/bin/update_deploy_repo
/etc/init.d/%{update_init}


%changelog
* Wed Jun 27 2012 Kenneth Lareau <klareau tagged com> - 0.1.0-1
- Initial version
