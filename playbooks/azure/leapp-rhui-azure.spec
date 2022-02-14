# Update name of package
%global provider    azure
Name:           leapp-rhui-%{provider}
Version:        1.0.0
Release:        1%{?dist}
Summary:        Leapp in-place upgrade cloud specific package
 
# Provider variable is name of subdirectory that is cloud specific, please
# refer to Leapp documentation/code for what subdir you should use.
# Examples: aws, azure
%global leappfilespath  %{_datadir}/leapp-repository/repositories/system_upgrade/common/files/rhui
 
License:        LGPLv2+
URL:            http://redhat.com
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}
 
BuildArch:      noarch
 
Requires:       leapp leapp-repository
 
# Update description
%description
Leapp in-place upgrade on %{provider}
 
%package sap
Summary: Leapp in-place upgrade cloud specific package (SAP)
Group:      System Environment/Base
%description sap
Leapp in-place upgrade of SAP on Azure.
 
%prep
%setup -q -n %{name}-%{version}
 
%build
 
%install
rm -rf $RPM_BUILD_ROOT
 
 
for provider in %{provider} %{provider}-sap
do
  mkdir -p %{buildroot}%{leappfilespath}/$provider
done
 
# leapp-%{provider}.repo is concatenation of rhui client .repo files
# that are necessary for RHEL8 clients to work.
cp src/leapp-%{provider}.repo  %{buildroot}%{leappfilespath}/%{provider}
# SAP
cp src/leapp-%{provider}-sap.repo  %{buildroot}%{leappfilespath}/%{provider}-sap
 
# Check your leapp-%{provider}.repo file for sslclientkey, sslclientcert and
# sslcacert lines - all unique files should be listed here.
 
# Base RHEL
cp src/key.pem %{buildroot}%{leappfilespath}/%{provider}
cp src/content.crt %{buildroot}%{leappfilespath}/%{provider}
 
# SAP Bundles
cp src/key-rhel8-sap-ha.pem %{buildroot}%{leappfilespath}/$provider
cp src/content-rhel8-sap-ha.crt %{buildroot}%{leappfilespath}/$provider
 
# Cloud specific yum/dnf plugins
%if %{provider} == "aws"
cp src/rhel7-dnf-plugin/amazon-id.py %{buildroot}%{leappfilespath}/%{provider}
%endif
 
exit 0
 
%files
%{leappfilespath}/%{provider}/key.pem
%{leappfilespath}/%{provider}/content.crt
%{leappfilespath}/%{provider}/leapp-%{provider}.repo
 
%if %{provider} == "aws"
%{leappfilespath}/%{provider}/amazon-id.py
%endif
 
%files sap
%{leappfilespath}/%{provider}-sap/key-rhel8-sap-ha.pem
%{leappfilespath}/%{provider}-sap/content-rhel8-sap-ha.crt
%{leappfilespath}/%{provider}-sap/leapp-%{provider}-sap.repo
 
%if %{provider} == "aws"
%{leappfilespath}/%{provider}-sap-eus/amazon-id.py
%endif
 
%changelog

