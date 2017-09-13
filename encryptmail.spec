%global username %{name}
%global groupname %{name}
%global homedir %{_sharedstatedir}/%{name}
# should mattch path used by postfix for alternatives
%global sendmail_path /usr/sbin/sendmail

%if 0%{?rhel} && 0%{?rhel} <= 6
%{!?__python2: %global __python2 /usr/bin/python2}
%{!?python2_sitelib: %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%{!?__python2: %global __python2 /usr/bin/python2}
%endif

%global selinux_types %(%{__awk} '/^#[[:space:]]*SELINUXTYPE=/,/^[^#]/ { if ($3 == "-") printf "%s ", $2 }' /etc/selinux/config 2>/dev/null)
%global selinux_variants %([ -z "%{selinux_types}" ] && echo mls targeted || echo %{selinux_types})
%{!?_selinux_policy_version: %global _selinux_policy_version %(sed -e 's,.*selinux-policy-\\([^/]*\\)/.*,\\1,' /usr/share/selinux/devel/policyhelp 2>/dev/null)}



Name:           encryptmail
Version:        0
Release:        0.13%{?dist}
Summary:        Simple MTA with GPG encryption support

License:        GPLv2+
URL:            https://github.com/tyll/encryptmail
Source0:        encryptmail-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python2-devel
# for systemd macros
BuildRequires:  systemd
BuildRequires:  selinux-policy-devel
BuildRequires:  checkpolicy
BuildRequires:  /usr/share/selinux/devel/policyhelp
BuildRequires:  hardlink
%if "%{_selinux_policy_version}" != ""
Requires:         selinux-policy >= %{_selinux_policy_version}
%endif
%if 0%{?rhel} || 0%{?fedora} < 23
Requires(post):   policycoreutils-python
Requires(postun): policycoreutils-python
%else
Requires(post):   policycoreutils-python-utils
Requires(postun): policycoreutils-python-utils
%endif


Requires:       pygpgme
Requires:       PyYAML
Requires(pre): shadow-utils
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd
Requires(post): %{_sbindir}/update-alternatives
Requires(postun): %{_sbindir}/update-alternatives
Requires(posttrans): /usr/sbin/semodule
Requires(posttrans): /sbin/fixfiles
Requires(postun): /usr/sbin/semodule
Requires(postun): /sbin/fixfiles



%description
Simple MTA to spool and encrypt mails for delivery via a smart host.


%prep
%setup -q


%build
%{__python2} setup.py build
cd selinux
for selinuxvariant in %{selinux_variants}
do
    make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile
    mv %{name}.pp %{name}.pp.${selinuxvariant}
    make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile clean
done
cd -


%install
rm -rf $RPM_BUILD_ROOT
%{__python2} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
%make_install prefix=%{_prefix}
mkdir -p $RPM_BUILD_ROOT%{_sbindir}
mkdir -p $(dirname $RPM_BUILD_ROOT%{sendmail_path})
touch $RPM_BUILD_ROOT%{sendmail_path}
for selinuxvariant in %{selinux_variants}
do
    install -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
    install -p -m 644 selinux/%{name}.pp.${selinuxvariant} \
        %{buildroot}%{_datadir}/selinux/${selinuxvariant}/%{name}.pp
done
/usr/sbin/hardlink -cv %{buildroot}%{_datadir}/selinux


%pre
getent group %{groupname} >/dev/null || groupadd -r %{groupname}
getent passwd %{username} >/dev/null || \
    useradd -r -g %{groupname} -d %{homedir} -s /sbin/nologin \
    -c "System account for %{name}" %{username}
exit 0


%post
%systemd_post %{name}.service
%{_sbindir}/update-alternatives --install %{sendmail_path} \
    mta %{_bindir}/encryptmail-sendmail 100


%preun
%systemd_preun %{name}.service


%postun
%systemd_postun_with_restart %{name}.service
if [ $1 -eq 0 ]; then
    %{_sbindir}/update-alternatives --remove mta %{_bindir}/encryptmail-sendmail
    for selinuxvariant in %{selinux_variants}
    do
        /usr/sbin/semodule -s ${selinuxvariant} -r %{name} &> /dev/null || :
    done
    /sbin/fixfiles -R %{name} restore > /dev/null 2>&1 || :
fi


%posttrans
for selinuxvariant in %{selinux_variants}
do
    /usr/sbin/semodule -s ${selinuxvariant} -i \
        %{_datadir}/selinux/${selinuxvariant}/%{name}.pp &> /dev/null || :
done
/sbin/fixfiles -R %{name} restore > /dev/null 2>&1 || :


%files
%{!?_licensedir:%global license %%doc}
%license gpl-2.0.txt gpl-3.0.txt
%doc
%{python2_sitelib}/*
%{_bindir}/encryptmail-mta
%{_bindir}/encryptmail-sendmail
%ghost %{sendmail_path}
%dir %{_sysconfdir}/encryptmail
%config(noreplace) %{_sysconfdir}/encryptmail/encryptmail.yaml
%attr(0700, %{username}, %{groupname}) %{_sharedstatedir}/encryptmail/
%attr(0700, %{username}, %{groupname}) %{_localstatedir}/spool/encryptmail
%attr(0755, %{username}, %{groupname}) %{_localstatedir}/run/encryptmail
%{_unitdir}/%{name}.service
%{_tmpfilesdir}/%{name}.conf
%{_datadir}/selinux/*/%{name}.pp


%changelog
* Mon Nov 16 2015 Till Maas <opensource@till.name> - 0.0
- initial spec file
