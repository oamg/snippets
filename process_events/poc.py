#!/usr/bin/python3

import os, json
from collections import namedtuple


FILE_PACKAGES = 'leapp-data.json'  # you need to download this separately because reasons
FILE_INSTALLED = 'base'
# FILE_INSTALLED = 'max-base'

Event = namedtuple('Event', ['action', 'in_pkgs', 'out_pkgs', 'initial_release', 'release'])
EVENT_TYPES = ('Present', 'Removed', 'Deprecated', 'Replaced', 'Split', 'Merged', 'Moved', 'Renamed')
RELEASES = ((7,5), (7,6), (7,7), (7,8), (8,0), (8,1), (8,2))


def print_event(e):
    print('{ir} -> {r}  {inp} --{ac}-> {out}'.format(
        ir=e.initial_release,
        r=e.release,
        inp=', '.join(p[0] for p in e.in_pkgs.items()) if e.in_pkgs else '{}',
        ac=e.action,
        out=', '.join(p[0] for p in e.out_pkgs.items()) if e.out_pkgs else '{}'
    ))


def print_triad(triad, name, limit=None):
    print(name)
    for key in 'to_keep', 'to_install', 'to_remove':
        print('    {}'.format(key))
        if not limit or len(triad[key]) < limit:
            for p in sorted(triad[key].items()):
                print('        {} :: {}'.format(p[0], p[1]))
        else:
            print('        <{} packages>'.format(len(triad[key])))
    print()


def parse_entry(entry):
    action = EVENT_TYPES[entry['action']]
    in_pkgs = {p['name']: p['repository'].lower() for p in entry['in_packageset']['package']}
    out_pkgs = {p['name']: p['repository'].lower() for p in entry['out_packageset']['package']} if entry['out_packageset'] else {}
    initial_release = (entry['initial_release']['major_version'], entry['initial_release']['minor_version']) if entry['initial_release'] else (0,0)
    release = (entry['release']['major_version'], entry['release']['minor_version']) if entry['release'] else (9,9)
    # we don't need archs here
    return Event(action, in_pkgs, out_pkgs, initial_release, release)


def filter_out_installed_pkgs(event_out_pkgs, installed_pkgs):
    return {k: v for k, v in event_out_pkgs.items() if k not in installed_pkgs}


def get_installed_out_pkgs(event_out_pkgs, installed_pkgs):
    return {k: v for k, v in event_out_pkgs.items() if k in installed_pkgs}


def filter_out_out_pkgs(event_in_pkgs, event_out_pkgs):
    return {k: v for k, v in event_in_pkgs.items() if k not in event_out_pkgs}


EVENTS = []
with open(FILE_PACKAGES) as f:
    data = json.load(f)
    EVENTS = [parse_entry(entry) for entry in data['packageinfo']]

INSTALLED = []
with open(FILE_INSTALLED) as f:
    INSTALLED = f.read().splitlines()       


total = { 'to_keep': {}, 'to_install': {}, 'to_remove': {} }


# for r in RELEASES:
for r in RELEASES:
    print()
    print(r, '-', len([e for e in EVENTS if e.release == r]), "eligible events")
    slated = { 'to_keep': {}, 'to_install': {}, 'to_remove': {} }
    print()

    for e in [e for e in EVENTS if e.release == r]:
        if all(
            p in INSTALLED + list(total['to_install'].keys())
                and p not in list(total['to_remove'].keys())
                for p in e.in_pkgs.keys()
        ):
            print_event(e)

            if e.action in ('Deprecated', 'Present'):
                for p, r in e.in_pkgs.items(): print('  KEEP {} :: {}'.format(p, r))
                slated['to_keep'].update(e.in_pkgs)

            if e.action == 'Moved':
                for p, r in e.out_pkgs.items(): print('  KEEP {} :: {}'.format(p, r))
                slated['to_keep'].update(e.out_pkgs)

            if e.action in ('Split', 'Merged', 'Renamed', 'Replaced'):
                not_installed = filter_out_installed_pkgs(e.out_pkgs, INSTALLED)
                installed = get_installed_out_pkgs(e.out_pkgs, INSTALLED)
                in_without_out = filter_out_out_pkgs(e.in_pkgs, e.out_pkgs)

                for p, r in not_installed.items(): print('  INSTALL {} :: {}'.format(p, r))
                slated['to_install'].update(not_installed)

                for p, r in installed.items(): print('  KEEP {} :: {}'.format(p, r))
                slated['to_keep'].update(installed)

                if e.action in ('Split', 'Merged'):
                    for p, r in in_without_out.items(): print('  REMOVE {} :: {}'.format(p, r))
                    slated['to_remove'].update(in_without_out)

            if e.action in ('Renamed', 'Replaced', 'Removed'):
                for p, r in e.in_pkgs.items(): print('  REMOVE {} :: {}'.format(p, r))
                slated['to_remove'].update(e.in_pkgs)

    if any(slated.values()):  # if there is anything in the subdicts of slated
        print()
        print_triad(total, 'TOTAL', limit=20)
        print_triad(slated, 'SLATED')

        print('Checking for conflicts')
        do_not_actually_remove = {}
        for p in slated['to_remove']:
            if p in total['to_keep']:
                print('  {} :: {} to be kept / slated for removal - unkeeping'.format(p, slated['to_remove'][p]))
                del total['to_keep'][p]
            elif p in total['to_install']:
                print('  {} :: {} to be installed / slated for removal - annihilating'.format(p, slated['to_remove'][p]))
                del total['to_install'][p]
                do_not_actually_remove[p] = slated['to_remove'][p]
        for p in do_not_actually_remove:
            del slated['to_remove'][p]
        print()

        print('Adding events')
        for key in 'to_keep', 'to_install', 'to_remove':
            total[key].update(slated[key])
        print()

        print_triad(total, 'TOTAL (updated)', limit=20)

    print(' ' + 20*'-=' + '-')


# unused = [p for p in INSTALLED if p not in total['to_remove'] and p not in total['to_keep']]
# if unused:
#     print()
#     print('Warning: {} packages have no applicable event'.format(len(unused)))
#     for p in unused:
#         print('  {}'.format(p))
