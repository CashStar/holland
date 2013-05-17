
# we don't do the condition check as per FPG because we are targeting
# el4 also... which doesn't support it
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

%{!?holland_version: %global holland_version 1.1.0a2}

# default %%rhel to make things easier to build
%{!?rhel: %global rhel %%(%{__sed} 's/^[^0-9]*\\([0-9]\\+\\).*/\\1/' /etc/redhat-release)}

# bcond compatibility macros for rhel4
%if %{!?with:1}0
%global with() %{expand:%%{?with_%{1}:1}%%{!?with_%{1}:0}}
%endif
%if %{!?without:1}0
%global without() %{expand:%%{?with_%{1}:0}%%{!?with_%{1}:1}}
%endif
%if %{!?bcond_with:1}0
%global bcond_with() %{expand:%%{?_with_%{1}:%%global with_%{1} 1}}
%endif
%if %{!?bcond_without:1}0
%global bcond_without() %{expand:%%{!?_without_%{1}:%%global with_%{1} 1}}
%endif

%bcond_without  tests
%bcond_with     sphinxdocs
%bcond_without  pgdump
%bcond_without  sqlite
%bcond_without  xtrabackup
%bcond_without  script
%bcond_with     delphini

Name:           holland
Version:        %{holland_version}
Release:        4%{?dist}
Summary:        Pluggable Backup Framework
Group:          Applications/Archiving
License:        BSD 
URL:            http://hollandbackup.org
Source0:        http://hollandbackup.org/releases/stable/1.0/%{name}-%{version}.tar.gz 
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python2-devel python-setuptools 
%if %{with sphinxdocs}
BuildRequires:  python-sphinx >= 1.0
%endif
%if %{with tests}
BuildRequires:  python-nose
%endif
Requires:       python-setuptools

%description
A pluggable backup framework which focuses on, but is not limited to, highly
configurable database backups.

%package common
Summary:        Common library functionality for Holland Plugins
License:        GPLv2
Group:          Applications/Archiving
Requires:       %{name} = %{version}-%{release} MySQL-python

%description common
Library for common functionality used by holland plugins


%package mysqldump
Summary: Logical mysqldump backup plugin for Holland
License: GPLv2
Group: Development/Libraries
Requires: %{name} = %{version}-%{release} %{name}-common = %{version}-%{release}

%description mysqldump
This plugin allows holland to perform logical backups of a MySQL database
using the mysqldump command.


%package mysqllvm
Summary: Holland LVM snapshot backup plugin for MySQL 
License: GPLv2
Group: Development/Libraries
Requires: %{name} = %{version}-%{release} %{name}-common = %{version}-%{release}
Provides: %{name}-lvm = %{version}-%{release}
Obsoletes: %{name}-lvm < 0.9.8
Requires: lvm2 MySQL-python tar

%description mysqllvm
This plugin allows holland to perform LVM snapshot backups of a MySQL database
and to generate a tar archive of the raw data directory.


%if %{with pgdump}
%package    pgdump
Summary: Holland LVM snapshot backup plugin for MySQL 
License: GPLv2
Group: Development/Libraries
Provides: %{name}-pgdump = %{version}-%{release}
Requires:   %{name} = %{version}-%{release} %{name}-common = %{version}-%{release}
Requires:   python-psycopg2

%description pgdump
This plugin allows holland to backup Postgres databases via the pg_dump command.
%endif

%if %{with sqlite}
%package sqlite
Summary: SQLite Backup Provider Plugin for Holland
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}
Requires: %{name}-common = %{version}-%{release}

%description sqlite 
SQLite Backup Provider Plugin for Holland
%endif

%if %{with xtrabackup}
%package xtrabackup
Summary: Xtrabackup plugin for Holland
License: GPLv2
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}
Requires: %{name}-common = %{version}-%{release}
Requires: xtrabackup >= 1.2

%description xtrabackup
This package provides a Holland plugin for the Percona Xtrabackup 
backup tool for InnoDB and XtraDB engines for MySQL
%endif

%if %{with script}
%package script
Summary: Shell script plugin for Holland
License: GPLv2
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}
Requires: %{name}-common = %{version}-%{release}

%description script
This package provides a Holland plugin that performs backups by
running a user supplied shell script command.
%endif

%if %{with delphini}
%package delphini
Summary: MySQL-Cluster plugin for Holland
License: GPLv2
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}
Requires: %{name}-common = %{version}-%{release}

%description delphini
This package provides a Holland plugin for MySQL-Cluster
in order to aggregate native backups from multiple data nodes.
%endif

%prep
%setup -q
mv plugins/README README.plugins
mv config/providers/README README.providers 

# cleanup, will be removed upstream at some point
rm plugins/ACTIVE

%build
%{__python} setup.py build

%if %{with sphinxdocs}
# docs
pushd docs
make html
make man
rm -f build/html/.buildinfo
popd
%endif

# library : holland.lib.common
cd plugins/holland.lib.common
%{__python} setup.py build
cd -
    
# library : holland.lib.mysql
cd plugins/holland.lib.mysql
%{__python} setup.py build
cd -

# library: holland.lib.lvm
cd plugins/holland.lib.lvm
%{__python} setup.py build
cd -

# plugin : holland.backup.mysqldump
cd plugins/holland.backup.mysqldump
%{__python} setup.py build
cd -

# plugin : holland.backup.mysql_lvm
cd plugins/holland.backup.mysql_lvm
%{__python} setup.py build
cd -

%if %{with pgdump}
cd plugins/holland.backup.pgdump
%{__python} setup.py build
cd -
%endif

# plugin : holland.backup.random
cd plugins/holland.backup.random
%{__python} setup.py build
cd -

%if %{with sqlite}
# plugin : holland.backup.sqlite
cd plugins/holland.backup.sqlite
%{__python} setup.py build
cd -
%endif

%if %{with xtrabackup}
cd plugins/holland.backup.xtrabackup
%{__python} setup.py build
cd -
%endif

%if %{with script}
cd plugins/holland.backup.script
%{__python} setup.py build
cd -
%endif

%if %{with delphini}
cd plugins/holland.backup.delphini
%{__python} setup.py build
cd -
%endif


%install
rm -rf %{buildroot}

%{__mkdir} -p   %{buildroot}%{_sysconfdir}/holland/{backupsets,providers} \
                %{buildroot}%{_localstatedir}/spool/holland \
                %{buildroot}%{_localstatedir}/log/holland/ \
                %{buildroot}%{_mandir}/man5


# holland-core
%{__python} setup.py install -O1 --skip-build --root %{buildroot} --install-scripts %{_sbindir}
install -m 0640 config/holland.conf %{buildroot}%{_sysconfdir}/holland/
%{__mkdir_p} -p %{buildroot}%{_mandir}/man1
%if %{with sphinxdocs}
install -m 0644 docs/build/man/holland.1 %{buildroot}%{_mandir}/man1
%endif
%{__mkdir_p} %{buildroot}%{python_sitelib}/holland/{lib,backup,commands,restore}

# library : holland.lib.common
cd plugins/holland.lib.common
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -
    
# library : holland.lib.mysql
cd plugins/holland.lib.mysql
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -

# library: holland.lib.lvm
cd plugins/holland.lib.lvm
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -

# plugin : holland.backup.mysqldump
cd plugins/holland.backup.mysqldump
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -
install -m 0640 config/providers/mysqldump.conf %{buildroot}%{_sysconfdir}/holland/providers/

# plugin : holland.backup.mysql_lvm
cd plugins/holland.backup.mysql_lvm
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -
install -m 0640 config/providers/mysql-lvm.conf %{buildroot}%{_sysconfdir}/holland/providers/

# plugin : holland.backup.pgdump
%if %{with pgdump}
cd plugins/holland.backup.pgdump
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -
install -m 0640 config/providers/pgdump.conf %{buildroot}%{_sysconfdir}/holland/providers/
%endif

%if %{with sqlite}
# plugin : holland.backup.sqlite
cd plugins/holland.backup.sqlite
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -
install -m 0640 config/providers/sqlite.conf %{buildroot}%{_sysconfdir}/holland/providers/
%endif

%if %{with xtrabackup}
# plugin : holland.backup.xtrabackup
cd plugins/holland.backup.xtrabackup
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -
install -m 0640 config/providers/xtrabackup.conf %{buildroot}%{_sysconfdir}/holland/providers/
%endif

%if %{with script}
# plugin : holland.backup.script
cd plugins/holland.backup.script
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -
install -m 0640 config/providers/script.conf %{buildroot}%{_sysconfdir}/holland/providers/
%endif

%if %{with delphini}
# plugin : holland.backup.delphini
cd plugins/holland.backup.delphini
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -
install -m 0640 config/providers/delphini.conf %{buildroot}%{_sysconfdir}/holland/providers/
%endif

# ensure we have no .pth files
rm -f %{buildroot}%{python_sitelib}/holland*nspkg.pth

# logrotate
%{__mkdir} -p %{buildroot}%{_sysconfdir}/logrotate.d
cat > %{buildroot}%{_sysconfdir}/logrotate.d/holland <<EOF
/var/log/holland.log /var/log/holland/holland.log {
    rotate 4
    weekly
    compress
    missingok
    create root adm
}
EOF

%if %{with tests}
%check
#%{__python} scripts/test_runner.py 
%endif

%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
%doc CHANGES.txt README.rst README.plugins README.providers 
%doc INSTALL LICENSE config/backupsets/examples/ 
%if %{with sphinxdocs}
%doc docs/build/html/
%endif
%{_sbindir}/holland
%dir %{python_sitelib}/holland/
%{python_sitelib}/holland/__init__.py*
%{python_sitelib}/holland/core/
%{python_sitelib}/holland/cli/
# XXX: this should probably move to a dev package
%{python_sitelib}/holland/devtools/
%{python_sitelib}/holland/test/
%{python_sitelib}/holland/backup/__init__.py*
%{python_sitelib}/holland/lib/__init__.py*
%{python_sitelib}/holland/commands/__init__.py*
%{python_sitelib}/holland-%{version}-*.egg-info
%if %{with sphinxdocs}
%{_mandir}/man1/holland.1*
%endif
%{_localstatedir}/log/holland/
%attr(0755,root,root) %dir %{_sysconfdir}/holland/
%attr(0755,root,root) %dir %{_sysconfdir}/holland/backupsets
%attr(0755,root,root) %dir %{_sysconfdir}/holland/providers
%attr(0640,root,root) %config(noreplace) %{_sysconfdir}/holland/holland.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/logrotate.d/holland
%attr(0755,root,root) %{_localstatedir}/spool/holland
# virtual namespaces
%dir %{python_sitelib}/holland/backup/
%dir %{python_sitelib}/holland/restore/
%dir %{python_sitelib}/holland/lib/

%files common
%defattr(-,root,root,-)
%doc plugins/holland.lib.common/{README,LICENSE}
%{python_sitelib}/%{name}/lib/compression.py*
%{python_sitelib}/%{name}/lib/archive/
%{python_sitelib}/%{name}/lib/hooks.py*
%{python_sitelib}/%{name}/lib/which.py*
%{python_sitelib}/%{name}/lib/mysql/
%{python_sitelib}/holland.lib.common-*.egg-info
%{python_sitelib}/holland.lib.mysql-*.egg-info

%files mysqldump
%defattr(-,root,root,-)
%doc plugins/holland.backup.mysqldump/{README,LICENSE}
%{python_sitelib}/holland/backup/mysqldump/
# XXX: hooks for testing 1.1a1
%{python_sitelib}/holland/lib/mysqldump/
%{python_sitelib}/holland.backup.mysqldump-*.egg-info
%config(noreplace) %{_sysconfdir}/holland/providers/mysqldump.conf

%files mysqllvm
%defattr(-,root,root,-)
%doc plugins/holland.backup.mysql_lvm/{README,LICENSE}
%{python_sitelib}/holland/backup/mysql*_lvm/
%{python_sitelib}/holland.backup.mysql*_lvm-*.egg-info
%{python_sitelib}/%{name}/lib/lvm/
%{python_sitelib}/holland.lib.lvm-*.egg-info
%config(noreplace) %{_sysconfdir}/holland/providers/mysql-lvm.conf

%if %{with pgdump}
%files pgdump
%defattr(-,root,root,-)
%doc plugins/holland.backup.pgdump/{README,LICENSE}
%{python_sitelib}/holland.backup.pgdump-*.egg-info
%{python_sitelib}/holland/backup/pgdump/
%config(noreplace) %{_sysconfdir}/holland/providers/pgdump.conf
%endif

%if %{with sqlite}
%files sqlite 
%defattr(-,root,root,-)
%doc plugins/holland.backup.sqlite/{README,LICENSE}
%{python_sitelib}/holland/backup/sqlite.py*
%{python_sitelib}/holland.backup.sqlite-*.egg-info
%config(noreplace) %{_sysconfdir}/holland/providers/sqlite.conf
%endif

%if %{with xtrabackup}
%files xtrabackup
%defattr(-,root,root,-)
%doc plugins/holland.backup.xtrabackup/{README,LICENSE}
%{python_sitelib}/holland/backup/xtrabackup/
%{python_sitelib}/holland.backup.xtrabackup-*.egg-info
%config(noreplace) %{_sysconfdir}/holland/providers/xtrabackup.conf
%endif

%if %{with script}
%files script
%defattr(-,root,root,-)
%doc plugins/holland.backup.script/{README,LICENSE}
%{python_sitelib}/holland/backup/script/
%{python_sitelib}/holland.backup.script*.egg-info
%config(noreplace) %{_sysconfdir}/holland/providers/script.conf
%endif

%if %{with delphini}
%files delphini
%defattr(-,root,root,-)
%doc plugins/holland.backup.delphini/{README,LICENSE}
%{python_sitelib}/holland/backup/delphini/
%{python_sitelib}/holland.backup.delphini*.egg-info
%config(noreplace) %{_sysconfdir}/holland/providers/delphini.conf
%endif


%changelog
* Thu May 18 2011 Andrew Garner <andrew.garner@rackspace.com> - 1.1.0-5
- holland/lib/multidict.py holland/lib/safefilename.py has been
  removed from the holland-common package

* Tue May 17 2011 Andrew Garner <andrew.garner@rackspace.com> - 1.1.0-4
- Include delphini backup plugin (conditionally built and off by default)
- Include script backup plugin

* Sun May 15 2011 Andrew Garner <andrew.garner@rackspace.com> - 1.1.0-3
- Include holland/test/ and holland/commands/ in holland package
- Include holland/lib/mysqldump in holland-mysqldump to pull in hooks
- Use new test_runner.py for running tests.

* Sun Feb 06 2011 Andrew Garner <andrew.garner@rackspace.com> - 1.1.0-2
- Run holland test suite by default (disable with --without tests)

* Sun Feb 06 2011 Andrew Garner <andrew.garner@rackspace.com> - 1.1.0-1
- Updating for holland-1.1
- Removed deprecated packages (mysqlhotcopy, maatkit, example)
- Added holland/cli and holland/devtools to main holland package
- Added holland/lib/hooks to holland-common package
- holland.1 manpage is now only included when using --with sphinxdocs

* Wed Jan 12 2011 BJ Dierkes <wdierkes@rackspace.com> - 1.0.7-1
- Development version

* Wed Jan 12 2011 BJ Dierkes <wdierkes@rackspace.com> - 1.0.6-1
- Latest sources from upstream.  Full change log available at:
  http://hollandbackup.org/releases/stable/1.0/CHANGES.txt
- ChangeLog became CHANGES.txt

* Tue Dec 14 2010 BJ Dierkes <wdierkes@rackspace.com> - 1.0.5-1
- Development version

* Tue Dec 14 2010 BJ Dierkes <wdierkes@rackspace.com> - 1.0.4-3
- Remove condition check around setting python_site{lib,arch} as
  it is not supported in el4.
- No longer set python_sitearch as we aren't using it

* Tue Nov 02 2010 BJ Dierkes <wdierkes@rackspace.com> - 1.0.4-2
- Make the example plugin optional (do not include by default)

* Tue Oct 26 2010 BJ Dierkes <wdierkes@rackspace.com> - 1.0.4-1
- Latest sources from upstream.
- No longer install /etc/holland/backupsets/examples, only keep it
  in %%doc
- Install config/providers/README to doc README.providers

* Thu Jul 08 2010 BJ Dierkes <wdierkes@rackspace.com> - 1.0.2-2
- Updated Source0 URL
- Updated python_sitelib/python_sitearch (per FPG)
- BuildRequires: python2-devel (per FPG)

* Thu Jul 08 2010 Andrew Garner <andrew.garner@rackspace.com> - 1.0.2-1
- Source updated to 1.0.2

* Tue Jul 06 2010 BJ Dierkes <wdierkes@rackspace.com> - 1.0.0-4
- Source update, 1.0.0 final
- Add ChangeLog back in under %%doc

* Thu Jul 01 2010 Andrew Garner <andrew.garner@rackspace.com> - 1.0.0-3.rc3
- Source updated to rc3

* Tue Jun 28 2010 Andrew Garner <andrew.garner@rackspace.com> - 1.0.0-2.rc2
- Source updated to rc2

* Thu Jun 11 2010 Andrew Garner <andrew.garner@rackspace.com> - 1.0.0-1.rc1
- Repackaging for release candidate
- Using conditional builds to exclude experimental plugins

* Tue Jun 08 2010 Andrew Garner <andrew.garner@rackspace.com> - 0.9.9-12
- Revert directory permissions back to standard 0755

* Sun Jun 06 2010 Andrew Garner <andrew.garner@rackspace.com> - 0.9.9-11
- Updated for changes from LVM cleanup

* Thu Jun 03 2010 Andrew Garner <andrew.garner@rackspace.com> - 0.9.9-10
- Added xtrabackup plugin

* Thu May 27 2010 BJ Dierkes <wdierkes@rackspace.com> - 0.9.9-9
- Move plugins/README to README.plugins and install via %%doc

* Mon May 25 2010 BJ Dierkes <wdierkes@rackspace.com> - 0.9.9-8
- Adding holland.lib.lvm under -common subpackage

* Wed May 19 2010 BJ Dierkes <wdierkes@rackspace.com> - 0.9.9-7
- BuildRequires: python-sphinx (to build docs)

* Mon May 17 2010 BJ Dierkes <wdierkes@rackspace.com> - 0.9.9-6
- Added sqlite plugin
- Loop over plugins rather than explicity build/install each.  Removes
  currently incomplete plugins first (pgdump)

* Fri May 14 2010 Tim Soderstrom <tsoderst@racksapce.com> - 0.9.9-5
- Added random plugin

* Mon May 10 2010 Andrew Garner <andrew.garner@rackspace.com> - 0.9.9-4
- Added missingok to holland.logrotate

* Sat May 8 2010 Andrew Garner <andrew.garner@rackspace.com> - 0.9.9-3
- Cleaned up /usr/share/docs/holland-* to only include html user documentation
  rather than everything in docs/
- /var/spool/holland and /var/log/holland/ are no longer world-readable
- /etc/holland/backupsets/examples is now a symlink to examples in the
  /usr/share/docs/holland-* directory
- The plugins/ACTIVE file is no longer used in order to have more flexibility
  in handling each individual plugin
- The setup.py --record mechanism is no longer used
- holland/{lib,commands,backup,restore} are now owned by the main holland
  package.

* Wed Apr 14 2010 Andrew Garner <andrew.garner@rackspace.com> - 0.9.9-2
- Updated rpm for new tree layout

* Tue Apr 13 2010 BJ Dierkes <wdierkes@rackspace.com> - 0.9.9-1.rs
- Removed -commvault subpackage
- Removed mysql-lvm config file hack
- Changed URL to http://hollandbackup.org
- No longer package plugins as eggs
- Conditionally BuildRequire: python-nose and run nose tests if _with_tests

* Thu Apr 07 2010 BJ Dierkes <wdierkes@rackspace.com> - 0.9.8-2.rs
- Rename holland-lvm to holland-mysqllvm, Obsoletes: holland-lvm
- Manually install mysql-lvm.conf provider config (fixed in 0.9.9)
- Install man files to _mandir
- Make logrotate.d/holland config(noreplace)

* Fri Apr 02 2010 BJ Dierkes <wdierkes@rackspace.com> - 0.9.8-1.rs
- Latest stable source from upstream.

* Wed Dec 09 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.7dev-1.rs
- Latest development trunk.
- Adding /etc/logrotate.d/holland logrotate script.

* Wed Dec 09 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.6-1.rs
- Latest stable sources from upstream.

* Fri Dec 04 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.5dev-1.rs
- Removing mysqlcmds by default
- Adding lvm subpackage

* Thu Oct 08 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.4-1.1.rs
- BuildRequires: python-dev
- Rebuilding for Fedora Core 

* Tue Sep 15 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.4-1.rs
- Latest sources.

* Mon Jul 13 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.3-1.rs
- Latest sources.

* Mon Jul 06 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.2-1.1.rs
- Rebuild

* Thu Jun 11 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.2-1.rs
- Latest sources from upstream.
- Only require epel for el4 (for now), and use PreReq rather than Requires.
- Require 'mysql' rather than 'mysqlclient'

* Wed Jun 03 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.1-1.rs
- Latest sources from upstream.
- Requires epel.

* Mon May 18 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.0-1.rs
- Latest from upstream
- Adding mysqlcmds package

* Tue May 05 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.4-1.2.rs
- Rebuild from trunk

* Sun May 03 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.4-1.1.rs
- Rebuild from trunk
- Adding commvault addon package.
- Removing Patch2: holland-0.3-config.patch
- Disable backupsets by default 

* Sat May 02 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.3.1-1.2.rs
- Build as noarch.

* Tue Apr 29 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.3.1-1.rs
- Latest sources.

* Tue Apr 28 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.3-1.rs
- Latest sources.
- Removed tests for time being
- Added Patch2: holland-0.3-config.patch
- Sub package holland-mysqldump obsoletes holland-mysql = 1.0.  Resolves
  tracker [#1189].

* Fri Apr 17 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.2-2.rs
- Rebuild.

* Wed Mar 11 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.2-1.rs
- Latest sources from upstream.

* Fri Feb 20 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.1.1.rs
- Updated with subpackages/plugins

* Wed Jan 28 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.1-1.rs
- Initial spec build
