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

%define __version %(%{__python} setup.py --version)
%define _pkg_version %(echo %{__version} | awk -F"-" '{print $1}')
%define _pkg_release %(echo %{__version} | awk -F"-" '{print "0." $2}')

%if "%{_pkg_release}" == "0."
%define _pkg_release 1
%endif

Name:           %{tagbase}-deploy
Version:        %{_pkg_version}
Release:        %{_pkg_release}%{?dist}
Summary:        Manage deployment of Tagged applications

Group:          Applications/Python
License:        MIT
URL:            None
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  %{pybase}-devel

Requires: %{tagbase}-tagopsdb
Requires: %{tagbase}-argparse
Requires: %{tagbase}-ordereddict


%description
Application to manage deployment of Tagged applications


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
# Note: use --install-scripts <path> for alternate location of programs
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/etc/init.d/
cp etc/%{update_init} $RPM_BUILD_ROOT/etc/init.d/%{update_init}
chmod +x $RPM_BUILD_ROOT/etc/init.d/%{update_init}
 

%clean
%{__python} setup.py clean --all
rm -rf $RPM_BUILD_ROOT


%package update-repo
Summary: Update repository daemon for deployment
Group: Applications/Python

Requires: %{tagbase}-tagopsdb
Requires: %{pybase}-simpledaemon

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
/usr/bin/unvalidated_deploy_check

%files update-repo
%defattr(-,root,root,-)
%doc
/usr/bin/update_deploy_repo
/etc/init.d/%{update_init}


%changelog
* Thu Sep 20 2012 Kenneth Lareau <klareau tagged com> - 0.8.5-1
- Initial release candidate with nearly all of the core features
  implemented
* Wed Jun 27 2012 Kenneth Lareau <klareau tagged com> - 0.1.0-1
- Initial version
