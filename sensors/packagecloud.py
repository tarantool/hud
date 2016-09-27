#!/usr/bin/env python3

import dateutil.parser
import datetime
import requests
import os
import pickle
import re
import sys
import yaml
import json

UPDATE_INTERVAL_SECONDS = 3600
NUM_TOP_PACKAGES = 5
PKGCLOUD_URL = 'https://packagecloud.io'
API_URL = 'https://packagecloud.io/api/v1'
EXTENSIONS = ['.rpm', '.deb']
PER_PAGE=1000

CACHE_FILE_NAME = 'packagecloud.cache'

CACHE = None

def read_cache():
    if not os.path.exists(CACHE_FILE_NAME):
        return {}

    with open (CACHE_FILE_NAME, 'rb') as f:
        result = pickle.load(f)
        return result

def write_cache(pkgs):
    with open(CACHE_FILE_NAME, 'wb') as f:
        pickle.dump(pkgs, f)

def get_repos(cfg):
    url = '%s/repos' % API_URL
    auth = (cfg['token'], '')

    r = requests.get( url, auth=auth)

    repos = [p['fqname'] for p in r.json()]

    return repos

def get_repo_packages(cfg, fqname):
    auth = (cfg['token'], '')

    result = []
    page = 1
    while True:
        url = '%s/repos/%s/packages.json?page=%d&per_page=%d' % (API_URL, fqname, page, PER_PAGE)
        r = requests.get( url, auth=auth)

        if not r.json():
            break
        for pkg in r.json():
            if os.path.splitext(pkg['filename'])[1] in EXTENSIONS:
                result.append(pkg)

        page += 1

    return result

def get_download_series(cfg, package):
    series_url = package['downloads_series_url']

    url = '%s/%s' % (PKGCLOUD_URL, series_url)
    auth = (cfg['token'], '')

    r = requests.get( url, auth=auth)
    series = r.json()['value']
    result = {}
    for key, value in series.items():
        result[dateutil.parser.parse(key.rstrip('Z')).date()] = \
            value

    return result

def update(cfg):
    global CACHE
    if not CACHE:
        CACHE = read_cache()

    cfg = cfg.copy()
    repos = get_repos(cfg)

    for repo in repos:
        packages = get_repo_packages(cfg, repo)
        for package in packages:
            url = package['package_html_url']
            today = datetime.date.today()

            if url not in CACHE:
                CACHE[url] = package

            if 'download_series' not in package:
                package['download_series'] = {}

            if today in CACHE[url]['download_series']:
                continue

            print ("Getting download series: ", package['filename'])
            series = get_download_series(cfg, package)
            package['download_series'].update(series)
            write_cache(CACHE)


def get(cfg):
    global CACHE
    if not CACHE:
        CACHE = read_cache()

    pkglist = list(CACHE.values())

    yesterday = datetime.date.today() - datetime.timedelta(days=1)


    pkglist = sorted(pkglist, key=
                     lambda x: x['download_series'][yesterday]
                     if yesterday in x['download_series'] else 0,
                     reverse=True)

    pkglist = pkglist[0: min(NUM_TOP_PACKAGES, len(pkglist))]
    result = []
    for pkg in pkglist:
        filename = re.sub("\\.g.*-", '-', pkg['filename'])
        result.append({'filename': filename,
                       'download_count': pkg['download_series'][yesterday],
                       'url': 'https://packagecloud.io' + pkg['package_html_url']})
    return result

def main():
    with open(sys.argv[1], 'r') as stream:
        cfg = yaml.load(stream)['packagecloud']

    update(cfg)
    pkgcloud = get(cfg)
    print(json.dumps(pkgcloud, indent=2))

if __name__ == '__main__':
    main()
