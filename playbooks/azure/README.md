# Enabling RHEL In-Place Upgrades with RHUI

## Building packages

This guide aims to help system engineers to enable RHEL 7 to RHEL 8 in-place upgrade using RHUI on not yet supported public cloud. It covers steps from identifying valid RHUI repository names, through building a special rpm package containing RHEL 8 repositories, changing a bit of Leapp code to add necessary mappings to actual in-place upgrade. 

1. Contact your internal RHUI team for the following purposes:
   1. Get RHEL 7 and RHEL 8 repository IDs.
   2. Sync RHEL 8.2 minor version into RHUI server in case only 8Server is synced.

2. Create repository mappings using the acquired repository IDs. The mapping will be later added into the “repomap.json” file downloaded in step #4. Leapp uses the “repomap.json” file to map RHEL X repositories to the corresponding RHEL X+1 repositories and enables them.
   * The repomap file is JSON file with the structure following this JSON schema:
https://raw.githubusercontent.com/oamg/schema-test/main/repomap-schema-test.json
Check that you find repoids of your repositories inside the file - in the repositories section. If not, you should add them inside. E.g. for RHEL 7 Base repository, find the related PESID (internal RH name, that cover family of repositories, in this case e.g. rhel7-base) with particular attributes (e.g. in case of azure, rhui attribute must contain azure). From the mapping part you can see to what target PESIDs it is going to be mapped. So under the specified target PESIDs,wanted repoids should be present as well with the same rhui attribute.

3. On top of that, we also need a mapping between your RHEL 7 and RHEL 8 RHUI client repository. These repositories that are not reflected by Red Hat CDN, usually need a special mapping to be added. Unless the expected client repositories are already present, the new mapping and pesids have to be added into the file as well. E.g. in this case the new pesids can be a random string or it can reflect the repoid it represents.
4. To upgrade from RHEL 7 to RHEL 8, Leapp needs access to RHEL 8 repositories (at least BaseOS, Appstream, and the RHEL 8 cloud-specific RHUI repo). To grant access, a special Leapp rpm package containing RHEL 8 repo file, corresponding certificates and keys is used to provide the data to Leapp.
   * **Example:** Create `leapp-<CLOUD_PROVIDER>.repo` file containing:

``` 
[rhui-rhel-8-for-x86_64-baseos-rhui-rpms]
name=Red Hat Enterprise Linux 8 for x86_64 - BaseOS from RHUI (RPMs)
baseurl=<YOUR_URL_CONTAINING_$RELEASEVER>
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release
sslverify=1
sslclientcert=/etc/pki/rhui/product/content.crt
sslclientkey=/etc/pki/rhui/private/key.pem

[rhui-rhel-8-for-x86_64-appstream-rhui-rpms]
name=Red Hat Enterprise Linux 8 for x86_64 - AppStream from RHUI (RPMs)
baseurl=<YOUR_URL_CONTAINING_$RELEASEVER>
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release
sslverify=1
sslclientcert=/etc/pki/rhui/product/content.crt
sslclientkey=/etc/pki/rhui/private/key.pem

[rhui-<CLOUD_PROVIDER>-rhel8]
name=<CLOUD_PROVIDER> RPMs for Red Hat Enterprise Linux 8
baseurl=<YOUR_URL_CONTAINING_$RELEASEVER>
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-release
sslverify=1
sslclientcert=/etc/pki/rhui/product/content.crt
sslclientkey=/etc/pki/rhui/private/key.pem
```
5. And corresponding “content.crt” and “key.pem” packaged in a tar file with the following structure:

```
src
├── content.crt
├── key.pem
├── leapp-<CLOUD_PROVIDER>.repo
```

6. Use the `leapp-rhui.spec` file in this directory to build your packages.

## Smoketest

Assuming you have a RHEL7 machine:

1. Enable “Extras” repository.
   * `# yum-config-manager --enable rhel-7-server-extras-rpms`
2. Install “leapp” and “leapp-repository” packages.
   * `# yum install -y leapp leapp-repository`
3. Download additional required data files from [this knowledge base article](https://access.redhat.com/articles/3664871)
   * Either production or free developer subscription is required to access the data.
4. Add the repository mapping you created to the `repomap.json` file saved in `/etc/leapp/files`

Now we need to update Leapp source code to tell it which package to use:

1. Edit `/usr/share/leapp-repository/repositories/system_upgrade/common/libraries/rhui.py`
2. Find `RHUI_CLOUD_MAP` in the file and add specifics of your cloud

| Name | Description |
| ---- | ----------- |
| `el7_pkg` | RHEL 7 cloud-specific RHUI rpm (used to detect RHUI/cloud) |
| `el8_pkg` | RHEL 8 cloud-specific RHUI rpm (used to detect RHUI/cloud) |
| `leapp_pkg` | Special Leapp RPM (created in step #6 above) that provides RHEL 8 repositories and certificates on RHEL 7 system |
| `leapp_pkg_repo` | Name of repository file provided in the `leapp-rhui-<CLOUD_PROVIDER>` RPM (See step 4. in **Building packages** above) |

3. Run the pre-upgrade assessment as described in [Reviewing the pre-upgrade report](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html-single/upgrading_from_rhel_7_to_rhel_8/index#reviewing-the-pre-upgrade-report_upgrading-from-rhel-7-to-rhel-8).
   * Resolve the following blockers:
     * Answer the `remove_pam_pkcs11_module_check` question in the answerfile as `True`
     * Add `PermitRootLogin yes` to the `/etc/ssh/sshd_config` file

4. Upgrade the system to RHEL 8. For more information, see [Performing the upgrade from RHEL 7 to RHEL 8](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html-single/upgrading_from_rhel_7_to_rhel_8/index#performing-the-upgrade-from-rhel-7-to-rhel-8_upgrading-from-rhel-7-to-rhel-8).







