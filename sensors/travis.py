#!/usr/bin/env python3

import requests
import sys
import yaml
import json

UPDATE_INTERVAL_SECONDS = 60
STATE = None

def get_repos(cfg):
    data={'active': False, 'limit': 1000}
    headers={'Authorization': 'token %s' % cfg['token']}
    url = '%s/repos/%s' % (cfg['url'], cfg['user'])

    r = requests.get( url, data=data, headers=headers)

    result = []
    for repo in r.json():
        status = 'unknown'
        if repo['last_build_status'] == 0:
            status = 'succeeded'
        if repo['last_build_status'] == 1:
            status = 'failed'

        build_number = repo['last_build_id']
        if build_number is None:
            continue
        build_url = 'http://travis-ci.org/%s/builds/%s' % (repo['slug'], build_number)
        result.append({'name': repo['slug'],
                       'status': status,
                       'url': build_url})
    return result

def update(cfg):
    global STATE
    cfg = cfg.copy()
    cfg['url'] = cfg.get('url', 'https://api.travis-ci.org')
    headers={'Authorization': 'token %s' % cfg['token']}
    url = '%s/repos/tarantool' % cfg['url']
    r = requests.get( url, headers=headers)

    repos = get_repos(cfg)

    result = {'successful_builds': [], 'failed_builds': []}
    for repo in repos:
        if repo['status'] == 'succeeded':
            result['successful_builds'].append(repo)
        if repo['status'] == 'failed':
            result['failed_builds'].append(repo)

    STATE = result
    return result


def get(cfg):
    global STATE
    if not STATE:
        STATE = {'successful_builds': [], 'failed_builds': []}

    return STATE


def main():
    with open(sys.argv[1], 'r') as stream:
        cfg = yaml.load(stream)['travis']

    update(cfg)
    travis = get(cfg)
    print(json.dumps(travis, indent=2))


if __name__ == '__main__':
    main()
