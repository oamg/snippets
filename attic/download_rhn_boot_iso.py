# This file was meant to be used with the Leapp actor framework

import os
import re
from datetime import datetime
from shutil import copyfileobj

from requests import Session
from six.moves import configparser

# from leapp.libraries.common.mounting import BindBount, LoopMount, OverlayMount, NullMount
from leapp.exceptions import StopActorExecutionError

LEAPP_BOOT_ISO_PATH = '/var/lib/leapp/boot.iso'
LEAPP_MOUNT_WORKDIR = '/var/run/leapp/mount'

_RE_LINKS = re.compile(r'href="(rhel-[^"]*-boot\.iso)"')

_UTCSTAMP = datetime.utcfromtimestamp(0)

_REPO_WHITELIST = (
    'rhel-8-for-x86_64-baseos-htb-rpms',
    'rhel-8-for-x86_64-baseos-rpms'
)

_VARIABLE_VALUES = (
    ('basearch', 'x86_64'),
    ('releasever', '8')
)


def _baseurl_fixup(data):
    values = dict(_VARIABLE_VALUES)
    for var in data.get('ui_repoid_vars', ' '.join(dict(_VARIABLE_VALUES).keys())).split():
        if var:
            data['baseurl'] = data['baseurl'].replace('$' + var, values[var])


def _find_repo(el7context):
    parser = configparser.ConfigParser()
    with el7context.open('/etc/yum.repos.d/redhat.repo', mode='r') as f:
        if hasattr(parser, 'read_file'):
            parser.read_file(
                f, f.name)  # pylint: disable=E1101; Disable warning for read_file in python2
        else:
            parser.readfp(f, f.name)

    for section in parser.sections():
        if section in _REPO_WHITELIST:
            print("Checking section: {}".format(section))
            if parser.has_option(section, 'enabled') and parser.getint(section, 'enabled') == 1:
                data = {}
                options = ('name', 'ui_repoid_vars', 'baseurl',
                           'sslclientkey', 'sslclientcert', 'sslcacert')
                required = ('name', 'baseurl')
                for option in options:
                    if parser.has_option(section, option):
                        data[option] = parser.get(section, option)
                if not all(option in data.keys() for option in required):
                    continue
                _baseurl_fixup(data)
                return data
    return None


def _get_stamp(r):
    """
    Exracts the Last-Modified header from the requests Response object and converts it to seconds since epoch.
    """
    return (datetime.strptime(r.headers.get('Last-Modified'), '%a, %d %b %Y %H:%M:%S %Z') - _UTCSTAMP).total_seconds()


def select_iso(session, url):
    """
    Checks for all available boot ISO images and selects the latest version.

    This is implemented by parsing the HTML content of the base_url which is the generated directory listing.
    From there the boot.iso names are filtered and on each of those is performed a HEAD request to get the headers
    with the last modification time.

    The last modified item is used.
    """
    response = session.get(url)
    images = []
    for iso in _RE_LINKS.findall(response.text):
        r = session.head(url=os.path.join(url, iso))
        images.append((iso, _get_stamp(r)))
    images.sort(key=lambda x: x[1])
    return images.pop()[0]


def download_bootiso(el7context, iso_path):
    repo_data = _find_repo(el7context)
    if not repo_data:
        return

    session = Session()
    if 'sslclientcert' in repo_data and 'sslclientkey' in repo_data:
        session.cert = (el7context.full_path(repo_data['sslclientcert']),
                        el7context.full_path(repo_data['sslclientkey']))
    if 'sslcacert' in repo_data:
        session.verify = el7context.full_path(repo_data['sslcacert'])

    base_url = os.path.join(repo_data['baseurl'], '../iso')
    selected_iso_url = os.path.join(base_url, select_iso(session, base_url))

    if not selected_iso_url:
        raise StopActorExecutionError(
            message='No suitable boot iso image seems to be available for download.')

    r = session.get(selected_iso_url, stream=True)
    with open(iso_path, 'wb') as fdst:
        copyfileobj(r.raw(), fdst)
