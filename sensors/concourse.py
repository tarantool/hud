#!/usr/bin/env python3

import requests
import sys
import yaml
import json

UPDATE_INTERVAL_SECONDS = 60
STATE = None

def list_teams(url):
    r = requests.get('%s/api/v1/teams' % url)

    teams = [team['name'] for team in r.json()]
    return teams

def team_login(url, team, auth):
    jar = requests.cookies.RequestsCookieJar()
    data = {'username': auth[0], 'password': auth[1]}
    session = requests.Session()
    r = session.post('%s/teams/%s/login' % (url, team), data=data)
    if r.status_code != 200:
        raise RuntimeError("Authentication failed as user '%s'" % auth[0])
    return session


def list_pipelines(session, url, team):
    r = session.get('%s/api/v1/teams/%s/pipelines' % (url, team))

    pipelines = [pipeline['name'] for pipeline in r.json()]
    return pipelines

def list_jobs(session, url, team, pipeline):
    r = session.get('%s/api/v1/teams/%s/pipelines/%s/jobs' %
                     (url, team, pipeline))

    result = []
    for job in r.json():
        status = "succeeded"
        job_url = job['url']
        num_failed = 0
        if 'finished_build' in job:
            status = job['finished_build']['status']
            job_url = job['finished_build']['url']

        if status != 'succeeded':
            r = session.get('%s/api/v1/teams/%s/pipelines/%s/jobs/%s/builds' %
                             (url, team, pipeline, job['name']))

            builds = r.json()
            builds = {int(build['name']): build for build in builds
                      if int(build['name']) <= int(job['finished_build']['name'])}

            for buildnum in reversed(list(builds.keys())):
                if builds[buildnum]['status'] == 'succeeded':
                    break
                num_failed += 1


        result.append({'name': job['name'],
                       'status': status,
                       'url': url + '/' + job_url,
                       'num_failed': num_failed})
    return result


def update(cfg):
    global STATE

    concourse = {'url': cfg['url'],
                 'successful_builds': [],
                 'failed_builds': []}

    url = cfg['url']
    auth = (cfg['username'], cfg['password'])
    teams = list_teams(url)

    for team in teams:
        session = team_login(url, team, auth)
        pipelines = list_pipelines(session, url, team)

        for pipeline in pipelines:
            jobs = list_jobs(session, url, team, pipeline)

            for job in jobs:
                job['team'] = team
                job['pipeline'] = pipeline

                if job['status'] == 'succeeded':
                    concourse['successful_builds'].append(job)
                else:
                    concourse['failed_builds'].append(job)
    STATE = concourse
    return STATE


def get(cfg):
    global STATE
    if not STATE:
        STATE = {'url': cfg['url'],
                 'successful_builds': [],
                 'failed_builds': []}

    return STATE


def main():
    with open(sys.argv[1], 'r') as stream:
        cfg = yaml.load(stream)['concourse']

    update(cfg)
    concourse = get(cfg)
    print(json.dumps(concourse, indent=2))

if __name__ == '__main__':
    main()
